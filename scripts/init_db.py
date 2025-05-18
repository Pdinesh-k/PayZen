from app.models import Base, Reward, User, Bill
from app.database import engine, SessionLocal
from app.auth import get_password_hash
from datetime import datetime, timedelta

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create test user if it doesn't exist
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
                reward_points=100
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print("Test user created successfully!")

            # Add sample bills for the test user
            sample_bills = [
                Bill(
                    biller_name="Electricity Board",
                    bill_type="Electricity",
                    amount=1500.00,
                    due_date=datetime.utcnow() + timedelta(days=7),
                    reminder_frequency=3,
                    owner_id=test_user.id
                ),
                Bill(
                    biller_name="Water Supply",
                    bill_type="Water",
                    amount=500.00,
                    due_date=datetime.utcnow() + timedelta(days=5),
                    reminder_frequency=3,
                    owner_id=test_user.id
                ),
                Bill(
                    biller_name="Internet Provider",
                    bill_type="Internet",
                    amount=999.00,
                    due_date=datetime.utcnow() + timedelta(days=-2),
                    reminder_frequency=3,
                    is_paid=True,
                    owner_id=test_user.id
                )
            ]
            
            for bill in sample_bills:
                db.add(bill)
            db.commit()
            print("Sample bills added successfully!")
        
        # Check if rewards already exist
        existing_rewards = db.query(Reward).first()
        if not existing_rewards:
            # Add sample rewards
            sample_rewards = [
                Reward(
                    name="Amazon Gift Card",
                    description="₹500 Amazon Gift Card",
                    points_required=1000,
                    is_active=True
                ),
                Reward(
                    name="Movie Tickets",
                    description="2 Movie Tickets worth ₹300 each",
                    points_required=500,
                    is_active=True
                ),
                Reward(
                    name="Food Voucher",
                    description="₹200 Food Delivery Voucher",
                    points_required=300,
                    is_active=True
                )
            ]
            
            for reward in sample_rewards:
                db.add(reward)
            
            db.commit()
            print("Sample rewards added successfully!")
        else:
            print("Rewards already exist in the database.")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 