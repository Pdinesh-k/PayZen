import logging
import traceback
import time
from app.main import app
from app import models
from app.database import engine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables with retry logic
def init_db(retries=3):
    """Initialize database with retry logic"""
    for attempt in range(retries):
        try:
            logger.info(f"Initializing database tables in run.py (attempt {attempt + 1}/{retries})...")
            models.Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully in run.py")
            return
        except Exception as e:
            logger.error(f"Error creating database tables in run.py (attempt {attempt + 1}): {str(e)}")
            if attempt == retries - 1:  # Last attempt
                logger.error(traceback.format_exc())
                raise
            time.sleep(1)  # Wait before retrying

# Initialize database
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize database in run.py: {str(e)}")
    # Don't raise the exception here, let the application start anyway
    # The tables will be created when they're first accessed

# This is used by Vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True) 