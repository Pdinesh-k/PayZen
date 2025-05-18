from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, email_utils
from .database import get_session_local
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_due_bills():
    """Check for bills that are due soon and send reminders."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Get all unpaid bills
        bills = db.query(models.Bill).filter(
            models.Bill.is_paid == False,
            models.Bill.due_date <= datetime.now() + timedelta(days=7)
        ).all()
        
        for bill in bills:
            # Get user
            user = db.query(models.User).filter(models.User.id == bill.owner_id).first()
            if user:
                # Send reminder email
                await email_utils.send_bill_reminder(
                    email=user.email,
                    bill_name=bill.biller_name,
                    amount=bill.amount,
                    due_date=bill.due_date.strftime("%Y-%m-%d")
                )
    finally:
        db.close()

def init_scheduler():
    """Initialize the APScheduler."""
    scheduler = AsyncIOScheduler()
    
    # Add jobs
    scheduler.add_job(
        check_due_bills,
        CronTrigger(hour=9),  # Run daily at 9 AM
        id='check_due_bills',
        name='Check bills due soon and send reminders',
        replace_existing=True
    )
    
    return scheduler 