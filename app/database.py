from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import time
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Determine if we're running on Vercel
IS_PRODUCTION = os.environ.get('VERCEL') == '1'

if IS_PRODUCTION:
    # Use PostgreSQL in production (Vercel)
    password = quote_plus("Valar9876@")  # URL encode the password
    # Force IPv4 by using the host IP instead of domain name
    DATABASE_URL = f"postgresql://postgres:{password}@34.87.166.243:5432/postgres"
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"

def get_engine(retries=3):
    """Create SQLAlchemy engine with retry logic"""
    for attempt in range(retries):
        try:
            if DATABASE_URL.startswith("sqlite"):
                return create_engine(
                    DATABASE_URL, connect_args={"check_same_thread": False}
                )
            else:
                # PostgreSQL configuration optimized for serverless
                return create_engine(
                    DATABASE_URL,
                    echo=True,  # Enable SQL logging
                    pool_pre_ping=True,  # Enable connection health checks
                    pool_size=1,  # Minimize connections for serverless
                    max_overflow=0,  # Disable overflow connections
                    pool_recycle=1800,  # Recycle connections every 30 minutes
                    pool_timeout=30,  # Connection timeout in seconds
                    connect_args={
                        "sslmode": "require",  # Force SSL connection
                        "connect_timeout": "30",  # Connection timeout in seconds
                        "application_name": "vercel_serverless"  # Identify the application
                    }
                )
        except Exception as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:  # Last attempt
                raise
            time.sleep(1)  # Wait before retrying

# Create engine with retry logic
try:
    engine = get_engine()
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Test the connection with proper text() wrapper
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Database connection error in get_db: {str(e)}")
        raise
    finally:
        db.close() 