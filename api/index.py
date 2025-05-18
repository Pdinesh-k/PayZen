from fastapi import FastAPI
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

error_message = None

try:
    from app.main import app
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "ok"}

except Exception as e:
    error_message = str(e)
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "error": error_message,
            "message": "Failed to load main application"
        }
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "error", "error": error_message}

# This file is specifically for Vercel deployment
# It imports our FastAPI app from the main application file 