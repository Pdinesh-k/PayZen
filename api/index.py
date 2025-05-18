from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.main import app
except Exception as e:
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"error": str(e)}
    
    @app.get("/debug")
    async def debug_info():
        return {
            "error": str(e),
            "sys.path": sys.path,
            "current_dir": os.getcwd(),
            "files_in_dir": os.listdir(os.getcwd()),
            "env_vars": dict(os.environ)
        }

# This file is required for Vercel serverless deployment 