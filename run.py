import logging
import traceback
import time
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pathlib
from app.main import app
from app import models
from app.database import engine, get_db
from fastapi import Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the absolute path to the static and templates directories
STATIC_DIR = str(pathlib.Path(__file__).parent / "app" / "static")
TEMPLATES_DIR = str(pathlib.Path(__file__).parent / "app" / "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates configuration
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Database connection error. Please try again later."}
        )

# This is used by Vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True) 