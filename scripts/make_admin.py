import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import User
from sqlalchemy.orm import Session

def make_user_admin(username: str, db: Session):
    """Make a user an admin by their username."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User '{username}' not found")
        return False
    
    user.is_admin = True
    db.commit()
    print(f"User '{username}' is now an admin")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    db = SessionLocal()
    try:
        make_user_admin(username, db)
    finally:
        db.close() 