from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, User, Bill, Reward, RewardClaim
from app.database import SQLALCHEMY_DATABASE_URL

def view_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    print("\n=== Users ===")
    users = db.query(User).all()
    for user in users:
        print(f"\nUser ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Active: {user.is_active}")
        print(f"Admin: {user.is_admin}")
        print(f"Reward Points: {user.reward_points}")

    print("\n=== Bills ===")
    bills = db.query(Bill).all()
    for bill in bills:
        print(f"\nBill ID: {bill.id}")
        print(f"Biller: {bill.biller_name}")
        print(f"Type: {bill.bill_type}")
        print(f"Amount: ${bill.amount}")
        print(f"Due Date: {bill.due_date}")
        print(f"Paid: {bill.is_paid}")
        print(f"Owner ID: {bill.owner_id}")

    print("\n=== Rewards ===")
    rewards = db.query(Reward).all()
    for reward in rewards:
        print(f"\nReward ID: {reward.id}")
        print(f"Name: {reward.name}")
        print(f"Description: {reward.description}")
        print(f"Points Required: {reward.points_required}")
        print(f"Active: {reward.is_active}")

    db.close()

if __name__ == "__main__":
    view_database() 