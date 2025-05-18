from fastapi import FastAPI
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "ok"}

except Exception as e:
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "error": str(e),
            "message": "Failed to load main application"
        }
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "error", "error": str(e)}

# This file is specifically for Vercel deployment
# It imports our FastAPI app from the main application file 