from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL', False)

if IS_PRODUCTION:
    # Use PostgreSQL in production (Vercel)
    # Try both environment variable names
    DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    if not DATABASE_URL:
        raise ValueError("Neither DATABASE_URL nor POSTGRES_URL environment variable is set in production")
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"

# Configure SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration with proper connection pooling for serverless
    engine = create_engine(
        DATABASE_URL,
        pool_size=1,  # Minimum pool size
        max_overflow=0,  # Disable overflow connections
        pool_timeout=30,  # Connection timeout in seconds
        pool_recycle=1800,  # Recycle connections every 30 minutes
        pool_pre_ping=True,  # Enable connection health checks
        connect_args={
            "sslmode": "require"  # Force SSL mode for Vercel deployment
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