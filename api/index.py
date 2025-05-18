from mangum import Mangum
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
    handler = Mangum(app, lifespan="off")
except Exception as e:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "error": str(e),
            "message": "Failed to load main application"
        }
    
    handler = Mangum(app, lifespan="off")

# This file is specifically for Vercel deployment
# It imports our FastAPI app from the main application file 