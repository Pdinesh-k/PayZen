import logging
import traceback
from app.main import app
from app import models
from app.database import engine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
try:
    logger.info("Initializing database tables in run.py...")
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully in run.py")
except Exception as e:
    logger.error(f"Error creating database tables in run.py: {str(e)}")
    logger.error(traceback.format_exc())

# This is used by Vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True) 