from app.database import get_session_local
from app.models import User

def make_admin(username):
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.is_admin = True
            db.commit()
            print(f"Successfully made {username} an admin!")
        else:
            print(f"User {username} not found!")
    finally:
        db.close()

if __name__ == "__main__":
    make_admin("pdinesh_k") 