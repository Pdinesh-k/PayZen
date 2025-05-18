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

def test_db_connection(host, port, timeout=10):
    """Test TCP connection to database"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"TCP connection test failed: {str(e)}")
        return False

if IS_PRODUCTION:
    # Use PostgreSQL in production (Vercel)
    password = quote_plus("Valar9876@")
    host = "34.87.166.243"
    port = 5432
    
    # Log connection attempt
    logger.info(f"Attempting to connect to PostgreSQL at {host}:{port}")
    
    # Test connection but don't fail if it doesn't work
    if not test_db_connection(host, port):
        logger.warning(f"Database port {port} is not reachable on {host}. Will retry during connection attempts.")
    
    DATABASE_URL = f"postgresql://postgres:{password}@{host}:{port}/postgres"
else:
    # Use SQLite in development
    DATABASE_URL = "sqlite:///./test.db"

def get_engine(retries=3):
    """Create SQLAlchemy engine with retry logic"""
    last_exception = None
    
    for attempt in range(retries):
        try:
            if DATABASE_URL.startswith("sqlite"):
                return create_engine(
                    DATABASE_URL, connect_args={"check_same_thread": False}
                )
            else:
                # PostgreSQL configuration optimized for serverless
                engine = create_engine(
                    DATABASE_URL,
                    echo=True,  # Enable SQL logging
                    pool_pre_ping=True,  # Enable connection health checks
                    pool_size=5,  # Increased pool size for better availability
                    max_overflow=10,  # Allow some overflow connections
                    pool_recycle=1800,  # Recycle connections every 30 minutes
                    pool_timeout=30,  # Increased connection timeout
                    connect_args={
                        "sslmode": "require",  # Force SSL connection
                        "connect_timeout": "30",  # Increased connection timeout
                        "keepalives": "1",  # Enable TCP keepalives
                        "keepalives_idle": "30",  # Idle time before sending keepalive
                        "keepalives_interval": "10",  # Time between keepalives
                        "keepalives_count": "3",  # Number of keepalive retries
                        "tcp_user_timeout": "30000",  # TCP timeout in milliseconds
                        "application_name": "vercel_serverless"
                    }
                )
                
                # Test the connection with increased timeout
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("Successfully connected to database")
                return engine
                
        except Exception as e:
            last_exception = e
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:  # Last attempt
                logger.error("All database connection attempts failed")
                raise
            time.sleep(min(5, 2 ** attempt))  # Exponential backoff capped at 5 seconds

# Create engine with retry logic
try:
    engine = get_engine()
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    if IS_PRODUCTION:
        logger.error("Database connection failed in production environment")
        raise
    else:
        logger.warning("Using SQLite as fallback in development")
        DATABASE_URL = "sqlite:///./test.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    for attempt in range(3):  # Try up to 3 times
        try:
            db = SessionLocal()
            # Test the connection
            db.execute(text("SELECT 1"))
            yield db
            break  # If successful, break the loop
        except Exception as e:
            logger.error(f"Database connection error in get_db (attempt {attempt + 1}): {str(e)}")
            if attempt == 2:  # Last attempt
                raise  # Re-raise the exception if all attempts fail
            time.sleep(1)  # Wait before retrying
        finally:
            db.close() 