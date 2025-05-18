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
        # Fallback to constructing URL from components
        db_user = os.environ.get('POSTGRES_USER', 'postgres')
        db_password = os.environ.get('POSTGRES_PASSWORD', 'Valar9876')
        db_host = os.environ.get('POSTGRES_HOST', 'db.yaegkkmbsxqpbjmjdqwu.supabase.co')
        db_port = os.environ.get('POSTGRES_PORT', '5432')
        db_name = os.environ.get('POSTGRES_DATABASE', 'postgres')
        
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Ensure SSL mode is set
    if '?' not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    elif 'sslmode=' not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
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