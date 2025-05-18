from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL', False)

if IS_PRODUCTION:
    # Use PostgreSQL in production (Vercel)
    DATABASE_URL = "postgresql://postgres:Valar9876@@db.yaegkkmbsxqpbjmjdqwu.supabase.co:5432/postgres"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 