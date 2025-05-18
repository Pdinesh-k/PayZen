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
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL') == '1'

# Get database configuration from environment variables
DB_CONNECTION_TIMEOUT = int(os.environ.get('DB_CONNECTION_TIMEOUT', '5'))
DB_MAX_RETRIES = int(os.environ.get('DB_MAX_RETRIES', '3'))
DB_RETRY_INTERVAL = int(os.environ.get('DB_RETRY_INTERVAL', '1'))

def get_db_url():
    """Get database URL based on environment"""
    if IS_PRODUCTION:
        # Use PostgreSQL in production (Vercel)
        password = quote_plus(os.environ.get('DB_PASSWORD', 'Valar9876@'))
        host = os.environ.get('DB_HOST', '34.87.166.243')
        user = os.environ.get('DB_USER', 'postgres')
        db_name = os.environ.get('DB_NAME', 'postgres')
        port = os.environ.get('DB_PORT', '5432')
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        # Use SQLite locally
        return "sqlite:///./sql_app.db"

def wait_for_db(max_retries=None, retry_interval=None):
    """Wait for database to become available"""
    retries = 0
    max_retries = max_retries or DB_MAX_RETRIES
    retry_interval = retry_interval or DB_RETRY_INTERVAL
    
    while retries < max_retries:
        try:
            # Try to connect using psycopg2 first
            if IS_PRODUCTION:
                conn = psycopg2.connect(
                    dbname=os.environ.get('DB_NAME', 'postgres'),
                    user=os.environ.get('DB_USER', 'postgres'),
                    password=os.environ.get('DB_PASSWORD', 'Valar9876@'),
                    host=os.environ.get('DB_HOST', '34.87.166.243'),
                    port=os.environ.get('DB_PORT', '5432'),
                    connect_timeout=DB_CONNECTION_TIMEOUT
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

# Create engine lazily
_engine = None

def get_engine():
    """Get SQLAlchemy engine with connection pooling and retry logic"""
    global _engine
    
    if _engine is not None:
        return _engine
        
    database_url = get_db_url()
    
    if IS_PRODUCTION:
        # Wait for database to be available with shorter timeout
        if not wait_for_db(max_retries=2, retry_interval=1):
            logger.warning("Proceeding without confirmed database connection")
    
    # Configure engine with appropriate settings for serverless
    _engine = create_engine(
        database_url,
        pool_pre_ping=True,     # Enable connection health checks
        pool_size=1,            # Minimal pool size for serverless
        max_overflow=0,         # No overflow connections in serverless
        pool_recycle=30,        # Recycle connections after 30 seconds
        pool_timeout=DB_CONNECTION_TIMEOUT,  # Connection timeout from env
        connect_args={
            "connect_timeout": DB_CONNECTION_TIMEOUT,  # PostgreSQL connection timeout
            "keepalives": 1,         # Enable TCP keepalive
            "keepalives_idle": 5,    # Idle time before sending keepalive
            "keepalives_interval": 1, # Interval between keepalives
            "keepalives_count": 3     # Number of keepalive attempts
        } if IS_PRODUCTION else {}
    )
    
    return _engine

# Create base class for declarative models
Base = declarative_base()

# Create session factory lazily
_SessionLocal = None

def get_session_local():
    """Get session factory lazily"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
            # Set session timeout to be less than Vercel's function timeout
            expire_on_commit=False
        )
    return _SessionLocal

@contextmanager
def get_db():
    """Get database session with automatic cleanup"""
    if not IS_PRODUCTION:
        # For local development, create tables if they don't exist
        Base.metadata.create_all(bind=get_engine())
        
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()