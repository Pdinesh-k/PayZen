import logging
import traceback
import time
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pathlib
from app.main import app
from app import models
from app.database import engine

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

# This is used by Vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True) 