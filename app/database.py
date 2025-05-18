from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import time
import logging
from urllib.parse import quote_plus
import socket

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
    host = "34.87.166.243"
    
    # Test TCP connection before attempting database connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((host, 5432))
        if result != 0:
            logger.error(f"Cannot establish TCP connection to {host}:5432")
            raise ConnectionError(f"Port 5432 is not open on {host}")
        sock.close()
    except Exception as e:
        logger.error(f"TCP connection test failed: {str(e)}")
        raise
        
    DATABASE_URL = f"postgresql://postgres:{password}@{host}:5432/postgres"
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"

def get_engine(retries=5):  # Increased retries
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
                    pool_recycle=300,  # Recycle connections every 5 minutes (reduced from 30)
                    pool_timeout=10,  # Reduced connection timeout
                    connect_args={
                        "sslmode": "require",  # Force SSL connection
                        "connect_timeout": "10",  # Reduced connection timeout
                        "tcp_keepalives": "1",  # Enable TCP keepalive
                        "tcp_keepalives_idle": "60",  # Seconds before sending keepalive
                        "tcp_keepalives_interval": "10",  # Seconds between keepalives
                        "tcp_keepalives_count": "3",  # Failed keepalive attempts before giving up
                        "application_name": "vercel_serverless"  # Identify the application
                    }
                )
        except Exception as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:  # Last attempt
                raise
            time.sleep(2 ** attempt)  # Exponential backoff: 1, 2, 4, 8, 16 seconds

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
        logger.info("Database connection test successful")
        yield db
    except Exception as e:
        logger.error(f"Database connection error in get_db: {str(e)}")
        raise
    finally:
        db.close() 