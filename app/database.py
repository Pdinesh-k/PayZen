from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import time
import logging
from urllib.parse import quote_plus
import socket
import psycopg2

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL') == '1'

def get_db_url():
    """Get database URL based on environment"""
    if IS_PRODUCTION:
        # Use PostgreSQL in production (Vercel)
        password = quote_plus("Valar9876@")  # URL encode the password
        host = "34.87.166.243"
        return f"postgresql://postgres:{password}@{host}:5432/postgres"
    else:
        # Use SQLite locally
        return "sqlite:///./sql_app.db"

def wait_for_db(max_retries=5, retry_interval=5):
    """Wait for database to become available"""
    retries = 0
    while retries < max_retries:
        try:
            # Try to connect using psycopg2 first
            if IS_PRODUCTION:
                conn = psycopg2.connect(
                    dbname="postgres",
                    user="postgres",
                    password="Valar9876@",
                    host="34.87.166.243",
                    port="5432",
                    connect_timeout=10
                )
                conn.close()
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.warning(f"Database connection attempt {retries + 1} failed: {str(e)}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Waiting {retry_interval} seconds before retrying...")
                time.sleep(retry_interval)
    
    logger.error("Failed to connect to database after maximum retries")
    return False

# Create SQLAlchemy engine with retry logic
def get_engine():
    """Get SQLAlchemy engine with connection pooling and retry logic"""
    database_url = get_db_url()
    
    if IS_PRODUCTION:
        # Wait for database to be available
        if not wait_for_db():
            logger.warning("Proceeding without confirmed database connection")
    
    # Configure engine with appropriate settings for serverless
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=5,         # Smaller pool size for serverless
        max_overflow=10,     # Allow some overflow connections
        pool_recycle=1800,   # Recycle connections after 30 minutes
        pool_timeout=30,     # Connection timeout of 30 seconds
        connect_args={
            "connect_timeout": 10,  # PostgreSQL connection timeout
            "keepalives": 1,        # Enable TCP keepalive
            "keepalives_idle": 30,  # Idle time before sending keepalive
            "keepalives_interval": 10,  # Interval between keepalives
            "keepalives_count": 5    # Number of keepalive attempts
        } if IS_PRODUCTION else {}
    )
    
    return engine

# Create engine instance
engine = get_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()