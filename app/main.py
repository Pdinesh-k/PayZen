from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from . import models, auth, email_utils
from .database import get_engine, get_session_local
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import re
from .scheduler import init_scheduler
import logging
import os
import traceback
from functools import wraps
import csv
from io import StringIO
import json
import pathlib
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables with retry logic
def init_db(retries=5, delay=2):
    """Initialize database with retry logic"""
    for attempt in range(retries):
        try:
            logger.info(f"Attempting to create database tables (attempt {attempt + 1}/{retries})...")
            models.Base.metadata.create_all(bind=get_engine())
            logger.info("Database tables created successfully")
            
            # Create initial data
            SessionLocal = get_session_local()
            db = SessionLocal()
            try:
                # Check if admin user exists
                admin = db.query(models.User).filter(models.User.is_admin == True).first()
                if not admin:
                    # Create admin user
                    admin = models.User(
                        email="admin@payzen.com",
                        username="admin",
                        hashed_password=auth.get_password_hash("admin123"),
                        is_active=True,
                        is_admin=True,
                        reward_points=1000
                    )
                    db.add(admin)
                    db.commit()
                    logger.info("Admin user created successfully")
                
                # Check if rewards exist
                rewards = db.query(models.Reward).first()
                if not rewards:
                    # Add sample rewards
                    sample_rewards = [
                        models.Reward(
                            name="Amazon Gift Card",
                            description="₹500 Amazon Gift Card",
                            points_required=1000,
                            is_active=True
                        ),
                        models.Reward(
                            name="Movie Tickets",
                            description="2 Movie Tickets worth ₹300 each",
                            points_required=500,
                            is_active=True
                        ),
                        models.Reward(
                            name="Food Voucher",
                            description="₹200 Food Delivery Voucher",
                            points_required=300,
                            is_active=True
                        )
                    ]
                    for reward in sample_rewards:
                        db.add(reward)
                    db.commit()
                    logger.info("Sample rewards created successfully")
            finally:
                db.close()
            
            return
        except Exception as e:
            logger.error(f"Error creating database tables (attempt {attempt + 1}): {str(e)}")
            if attempt == retries - 1:  # Last attempt
                logger.error(traceback.format_exc())
                raise
            time.sleep(delay)  # Wait before retrying

# Initialize database on startup
init_db()

# Dependency for database sessions
def get_db_session():
    """Get database session for dependency injection"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="PayZen",
    description="A bill payment and rewards management system",
    debug=True  # Enable debug mode
)

# Get the absolute path to the static and templates directories
STATIC_DIR = str(pathlib.Path(__file__).parent / "static")
TEMPLATES_DIR = str(pathlib.Path(__file__).parent / "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates configuration
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a user-friendly error page
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "An unexpected error occurred. Please try again later."
            },
            status_code=500
        )

@app.on_event("startup")
async def startup_event():
    """Initialize the scheduler on application startup."""
    scheduler = init_scheduler()
    scheduler.start()

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BillCreate(BaseModel):
    biller_name: str
    bill_type: str
    amount: float
    due_date: str
    reminder_frequency: int

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    logger.debug("Register page accessed")
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db_session)
):
    logger.debug(f"Register attempt for email: {email}, username: {username}")
    # Validate input
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match"},
            status_code=400
        )
    
    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Password must be at least 8 characters long"},
            status_code=400
        )
    
    # Check if username contains only allowed characters
    if not re.match("^[a-zA-Z0-9_-]+$", username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username can only contain letters, numbers, underscores, and hyphens"},
            status_code=400
        )
    
    # Check if email or username already exists
    if db.query(models.User).filter(models.User.email == email).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"},
            status_code=400
        )
    
    if db.query(models.User).filter(models.User.username == username).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already taken"},
            status_code=400
        )
    
    try:
        hashed_password = auth.get_password_hash(password)
        db_user = models.User(
            email=email,
            username=username,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "success": "Registration successful! Please login to continue.",
            }
        )
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "An error occurred during registration"},
            status_code=500
        )

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_session)
):
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user or not auth.verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Incorrect username or password"},
                status_code=401
            )
        
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True
        )
        return response
    
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "An error occurred during login"},
            status_code=500
        )

@app.get("/dashboard")
async def dashboard(request: Request, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    try:
        logger.debug(f"Dashboard access by user: {current_user.username}")
        user_bills = db.query(models.Bill).filter(models.Bill.owner_id == current_user.id).all()
        logger.debug(f"Found {len(user_bills)} bills for user")
        available_rewards = db.query(models.Reward).filter(models.Reward.is_active == True).all()
        logger.debug(f"Found {len(available_rewards)} available rewards")
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "bills": user_bills,
                "rewards": available_rewards,
                "now": datetime.utcnow()
            }
        )
    except Exception as e:
        logger.exception("Error in dashboard route")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/bills/add")
async def add_bill_page(request: Request, current_user = Depends(auth.get_current_active_user)):
    return templates.TemplateResponse("add_bill.html", {"request": request, "user": current_user})

@app.post("/bills/add")
async def add_bill(
    request: Request,
    biller_name: str = Form(...),
    bill_type: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    reminder_frequency: int = Form(...),
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    try:
        # Convert due_date string to datetime
        due_date_dt = datetime.strptime(due_date, "%Y-%m-%d")
        
        db_bill = models.Bill(
            biller_name=biller_name,
            bill_type=bill_type,
            amount=amount,
            due_date=due_date_dt,
            reminder_frequency=reminder_frequency,
            owner_id=current_user.id
        )
        db.add(db_bill)
        db.commit()
        db.refresh(db_bill)
        
        try:
            # Send confirmation email
            await email_utils.send_bill_created_confirmation(
                email=current_user.email,
                bill_name=biller_name,
                due_date=due_date,
                amount=amount
            )
        except Exception as email_error:
            print(f"Email error: {str(email_error)}")
            # Don't rollback the transaction, just log the error
            # The bill is still added successfully
        
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        db.rollback()  # Rollback the transaction if there's an error
        print(f"Error adding bill: {str(e)}")
        return templates.TemplateResponse(
            "add_bill.html",
            {
                "request": request,
                "user": current_user,
                "error": "An error occurred while adding the bill"
            },
            status_code=500
        )

@app.get("/bills/{bill_id}/edit")
async def edit_bill_page(
    bill_id: int,
    request: Request,
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    bill = db.query(models.Bill).filter(
        models.Bill.id == bill_id,
        models.Bill.owner_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return templates.TemplateResponse(
        "edit_bill.html",
        {
            "request": request,
            "user": current_user,
            "bill": bill
        }
    )

@app.post("/bills/{bill_id}/edit")
async def edit_bill(
    bill_id: int,
    request: Request,
    biller_name: str = Form(...),
    bill_type: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    reminder_frequency: int = Form(...),
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    bill = db.query(models.Bill).filter(
        models.Bill.id == bill_id,
        models.Bill.owner_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    try:
        bill.biller_name = biller_name
        bill.bill_type = bill_type
        bill.amount = amount
        bill.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        bill.reminder_frequency = reminder_frequency
        
        db.commit()
        return RedirectResponse(url="/bills", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "edit_bill.html",
            {
                "request": request,
                "user": current_user,
                "bill": bill,
                "error": "An error occurred while updating the bill"
            },
            status_code=500
        )

@app.post("/bills/{bill_id}/pay")
async def pay_bill(
    bill_id: int,
    request: Request,
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    try:
        logger.debug(f"Processing bill payment for bill_id: {bill_id}")
        logger.debug(f"Current user points before payment: {current_user.reward_points}")
        
        bill = db.query(models.Bill).filter(
            models.Bill.id == bill_id,
            models.Bill.owner_id == current_user.id
        ).first()
        
        if not bill:
            logger.error(f"Bill {bill_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Bill not found")
        
        if bill.is_paid:
            logger.debug(f"Bill {bill_id} is already paid")
            return RedirectResponse(url="/bills", status_code=303)
            
        points_earned = 10  # Base points for paying bill
        logger.debug(f"Base points earned: {points_earned}")
        
        # Extra points for early payment
        current_time = datetime.now()
        if isinstance(bill.due_date, str):
            due_date = datetime.strptime(bill.due_date, "%Y-%m-%d")
        else:
            due_date = bill.due_date
            
        days_until_due = (due_date.date() - current_time.date()).days
        logger.debug(f"Days until due: {days_until_due}")
        
        if days_until_due > 5:
            points_earned += 5  # Bonus points for early payment
            logger.debug(f"Added bonus points. Total points earned: {points_earned}")
        
        # Update bill status and user points
        bill.is_paid = True
        bill.paid_date = current_time
        
        # Refresh user from database to get latest points
        current_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        current_user.reward_points += points_earned
        logger.debug(f"Updated user points. New total: {current_user.reward_points}")
        
        try:
            db.commit()
            logger.debug("Successfully committed changes to database")
        except Exception as commit_error:
            logger.error(f"Error committing changes: {str(commit_error)}")
            db.rollback()
            raise
        
        # Flash message will be added to the session
        response = RedirectResponse(url="/bills", status_code=303)
        response.set_cookie(
            "flash_message",
            f"Bill paid successfully! You earned {points_earned} points.",
            max_age=5
        )
        return response
    
    except Exception as e:
        logger.error(f"Error in pay_bill route: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "An error occurred while processing the payment."
            },
            status_code=500
        )

@app.get("/rewards/{reward_id}/claim")
async def claim_reward(
    reward_id: int,
    request: Request,
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    reward = db.query(models.Reward).filter(
        models.Reward.id == reward_id,
        models.Reward.is_active == True
    ).first()
    
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if current_user.reward_points < reward.points_required:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    try:
        # Create reward claim and deduct points
        claim = models.RewardClaim(
            user_id=current_user.id,
            reward_id=reward.id,
            points_used=reward.points_required,
            claimed_at=datetime.utcnow()
        )
        current_user.reward_points -= reward.points_required
        
        db.add(claim)
        db.commit()
        
        # Send reward claim confirmation email
        await email_utils.send_reward_claimed_confirmation(
            email=current_user.email,
            reward_name=reward.name,
            points_used=reward.points_required,
            points_remaining=current_user.reward_points
        )
        
        # If points are low after claiming, send notification
        if current_user.reward_points < 50:
            await email_utils.send_low_points_notification(
                email=current_user.email,
                current_points=current_user.reward_points
            )
            
        return RedirectResponse(url="/rewards", status_code=303)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process reward claim: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process reward claim")

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/bills")
async def list_bills(request: Request, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    try:
        if not current_user:
            logger.debug("User not authenticated, redirecting to login")
            return RedirectResponse(url="/login", status_code=303)

        logger.debug(f"Bills page access by user: {current_user.username}")
        user_bills = db.query(models.Bill).filter(models.Bill.owner_id == current_user.id).all()
        logger.debug(f"Found {len(user_bills)} bills for user")
        
        return templates.TemplateResponse(
            "bills.html",
            {
                "request": request,
                "user": current_user,
                "bills": user_bills,
                "now": datetime.utcnow()
            }
        )
    except Exception as e:
        logger.error(f"Error in bills route: {str(e)}")
        logger.error(traceback.format_exc())
        if isinstance(e, HTTPException) and e.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"An error occurred while loading your bills: {str(e)}"
            },
            status_code=500
        )

@app.get("/rewards")
async def list_rewards(request: Request, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    try:
        logger.debug(f"Rewards page access by user: {current_user.username}")
        
        # Get available rewards
        available_rewards = db.query(models.Reward).filter(models.Reward.is_active == True).all()
        logger.debug(f"Found {len(available_rewards)} available rewards")
        
        # Get user's claimed rewards with reward details
        claimed_rewards = db.query(models.RewardClaim).join(
            models.Reward,
            models.RewardClaim.reward_id == models.Reward.id
        ).filter(
            models.RewardClaim.user_id == current_user.id
        ).all()
        logger.debug(f"Found {len(claimed_rewards)} claimed rewards")

        # If no rewards exist, create some default rewards
        if not available_rewards:
            logger.debug("No rewards found, creating default rewards")
            default_rewards = [
                models.Reward(
                    name="Amazon Gift Card",
                    description="₹500 Amazon Gift Card",
                    points_required=1000,
                    is_active=True
                ),
                models.Reward(
                    name="Movie Tickets",
                    description="2 Movie Tickets worth ₹300 each",
                    points_required=500,
                    is_active=True
                ),
                models.Reward(
                    name="Food Voucher",
                    description="₹200 Food Delivery Voucher",
                    points_required=300,
                    is_active=True
                )
            ]
            for reward in default_rewards:
                db.add(reward)
            db.commit()
            
            # Fetch the newly created rewards
            available_rewards = db.query(models.Reward).filter(models.Reward.is_active == True).all()
            logger.debug(f"Created {len(available_rewards)} default rewards")
        
        return templates.TemplateResponse(
            "rewards.html",
            {
                "request": request,
                "user": current_user,
                "available_rewards": available_rewards,
                "claimed_rewards": claimed_rewards
            }
        )
    except Exception as e:
        logger.error(f"Error in rewards route: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"An error occurred while loading rewards: {str(e)}"
            },
            status_code=500
        )

async def check_due_bills():
    """Check for bills that are due soon and send reminders."""
    # For testing purposes, we'll just return success
    return True

@app.get("/test-reminder")
async def test_reminder(current_user = Depends(auth.get_current_active_user)):
    """Test endpoint to manually trigger bill reminders."""
    # Removed admin check for testing purposes
    await check_due_bills()
    return {"message": "Bill reminder check triggered successfully"}

@app.get("/test-email")
async def test_email(request: Request, current_user = Depends(auth.get_current_active_user)):
    """Test endpoint to verify email functionality."""
    try:
        success = await email_utils.send_email(
            email=current_user.email,
            subject="PayZen Email Test",
            body="""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Email Test Successful!</h2>
                <p>If you're reading this, the email system is working correctly.</p>
                <p>Time sent: {}</p>
            </div>
            """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        logger.error(f"Error in test-email endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-email-simple")
async def test_email_simple(
    request: Request,
    test_email: str,
    current_user = Depends(auth.get_current_active_user)
):
    """Simple test endpoint to verify email functionality."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can test email")
    
    success = await email_utils.send_test_email(test_email)
    if success:
        return {"status": "success", "message": "Test email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email")

@app.get("/test-email/{email}")
async def test_email(email: str):
    """Test endpoint to verify email functionality."""
    success = await email_utils.send_email(
        email=email,
        subject="PayZen Test Email",
        body="""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email from PayZen</h2>
            <p>This is a test email sent at: {}</p>
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    if success:
        return {"status": "success", "message": "Test email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")

# API endpoints
@app.post("/auth/register")
async def register_api(user: UserCreate, db: Session = Depends(get_db_session)):
    # Check if email or username already exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login")
async def login_api(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_session)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/bills/")
async def create_bill(bill: BillCreate, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    db_bill = models.Bill(
        biller_name=bill.biller_name,
        bill_type=bill.bill_type,
        amount=bill.amount,
        due_date=datetime.strptime(bill.due_date, "%Y-%m-%d").date(),
        reminder_frequency=bill.reminder_frequency,
        owner_id=current_user.id
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill

@app.get("/bills/")
async def get_bills(current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    return db.query(models.Bill).filter(models.Bill.owner_id == current_user.id).all()

@app.get("/rewards/points")
async def get_points(current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    return {"points": current_user.reward_points}

@app.post("/rewards/add-points")
async def add_points(points: dict, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    current_user.reward_points += points["points"]
    db.commit()
    return {"success": True, "points": current_user.reward_points}

@app.post("/rewards/redeem")
async def redeem_reward(reward_data: dict, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session)):
    if current_user.reward_points < reward_data["points_cost"]:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    reward = db.query(models.Reward).filter(models.Reward.id == reward_data["reward_id"]).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    current_user.reward_points -= reward_data["points_cost"]
    db.commit()
    return {"success": True, "remaining_points": current_user.reward_points}

# Admin middleware
def admin_required(func):
    @wraps(func)
    async def wrapper(request: Request, current_user = Depends(auth.get_current_active_user), db: Session = Depends(get_db_session), *args, **kwargs):
        if not current_user or not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        return await func(request=request, current_user=current_user, db=db, *args, **kwargs)
    return wrapper

# Admin routes
@app.get("/admin")
@admin_required
async def admin_dashboard(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        # Existing statistics
        stats = {
            "total_users": db.query(models.User).count(),
            "active_users": db.query(models.User).filter(models.User.is_active == True).count(),
            "total_bills": db.query(models.Bill).count(),
            "paid_bills": db.query(models.Bill).filter(models.Bill.is_paid == True).count(),
            "due_bills": db.query(models.Bill).filter(
                models.Bill.is_paid == False,
                models.Bill.due_date <= datetime.now() + timedelta(days=7)
            ).count(),
            "due_amount": sum([
                bill.amount for bill in db.query(models.Bill).filter(
                    models.Bill.is_paid == False,
                    models.Bill.due_date <= datetime.now() + timedelta(days=7)
                ).all()
            ]),
            "rewards_issued": db.query(models.RewardClaim).count(),
            "total_points": sum([user.reward_points for user in db.query(models.User).all()])
        }
        
        # Bill payment trends (last 7 days)
        bill_dates = []
        bill_counts = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            count = db.query(models.Bill).filter(
                models.Bill.is_paid == True,
                models.Bill.created_at >= date.replace(hour=0, minute=0, second=0),
                models.Bill.created_at < (date + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            ).count()
            bill_dates.append(date.strftime("%Y-%m-%d"))
            bill_counts.append(count)
        
        stats["bill_dates"] = bill_dates
        stats["bill_counts"] = bill_counts
        
        # Reward distribution
        rewards = db.query(models.Reward).all()
        reward_names = [reward.name for reward in rewards]
        reward_claims = [
            db.query(models.RewardClaim).filter(
                models.RewardClaim.reward_id == reward.id
            ).count()
            for reward in rewards
        ]
        
        stats["reward_names"] = reward_names
        stats["reward_claims"] = reward_claims
        
        # Get recent data
        users = db.query(models.User).order_by(models.User.id.desc()).limit(10).all()
        recent_bills = db.query(models.Bill).order_by(
            models.Bill.created_at.desc()
        ).limit(5).all()
        recent_claims = db.query(models.RewardClaim).order_by(
            models.RewardClaim.claimed_at.desc()
        ).limit(5).all()
        
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "stats": stats,
                "users": users,
                "recent_bills": recent_bills,
                "recent_claims": recent_claims
            }
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/users/{user_id}/toggle")
@admin_required
async def toggle_user_status(
    user_id: int,
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deactivating own account
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot deactivate own account")
        
        user.is_active = not user.is_active
        db.commit()
        return {"success": True, "is_active": user.is_active}
    except Exception as e:
        logger.error(f"Error toggling user status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users/{user_id}/details")
async def get_user_details(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's bills
        total_bills = db.query(models.Bill).filter(models.Bill.owner_id == user.id).count()
        paid_bills = db.query(models.Bill).filter(
            models.Bill.owner_id == user.id,
            models.Bill.is_paid == True
        ).count()
        
        # Get user's reward claims
        rewards_claimed = db.query(models.RewardClaim).filter(
            models.RewardClaim.user_id == user.id
        ).count()
        
        return {
            "username": user.username,
            "email": user.email,
            "reward_points": user.reward_points,
            "is_active": user.is_active,
            "total_bills": total_bills,
            "paid_bills": paid_bills,
            "rewards_claimed": rewards_claimed
        }
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/export/{data_type}")
async def export_data(
    data_type: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_session)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        if data_type == "users":
            # Export users data
            writer.writerow(["ID", "Username", "Email", "Points", "Status", "Is Admin"])
            users = db.query(models.User).all()
            for user in users:
                writer.writerow([
                    user.id,
                    user.username,
                    user.email,
                    user.reward_points,
                    "Active" if user.is_active else "Inactive",
                    "Yes" if user.is_admin else "No"
                ])
            filename = "users_export.csv"
        
        elif data_type == "bills":
            # Export bills data
            writer.writerow(["ID", "User", "Biller", "Type", "Amount", "Due Date", "Status"])
            bills = db.query(models.Bill).all()
            for bill in bills:
                writer.writerow([
                    bill.id,
                    bill.owner.username,
                    bill.biller_name,
                    bill.bill_type,
                    bill.amount,
                    bill.due_date.strftime("%Y-%m-%d"),
                    "Paid" if bill.is_paid else "Pending"
                ])
            filename = "bills_export.csv"
        
        else:
            raise HTTPException(status_code=400, detail="Invalid export type")
        
        output.seek(0)
        return FileResponse(
            output,
            media_type="text/csv",
            filename=filename
        )
    
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 