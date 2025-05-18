from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL') == '1'

if IS_PRODUCTION:
    # Use PostgreSQL in production (Vercel)
    DATABASE_URL = "postgresql://postgres:Valar9876%40@db.yaegkkmbsxqpbjmjdqwu.supabase.co:5432/postgres"
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"

# Configure SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration optimized for serverless
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=1,  # Minimize connections for serverless
        max_overflow=0,  # Disable overflow connections
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "sslmode": "require",  # Force SSL connection
            "connect_timeout": 10,  # Connection timeout in seconds
            "keepalives": 1,  # Enable keepalive
            "keepalives_idle": 30,  # Idle time before sending keepalive
            "keepalives_interval": 10,  # Interval between keepalives
            "keepalives_count": 5,  # Number of keepalive retries
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 