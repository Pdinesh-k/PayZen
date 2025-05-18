from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import sys
import os
import psycopg2
import sqlalchemy.exc
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

error_message = None

try:
    from app.main import app
    
    # Mount static directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(os.path.join(static_dir, "favicon.png"))
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "ok", "environment": os.environ.get("ENVIRONMENT", "production")}

    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except (psycopg2.OperationalError, sqlalchemy.exc.OperationalError) as e:
            logger.error(f"Database error: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Database connection error. Please try again later.",
                    "detail": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "An unexpected error occurred.",
                    "detail": str(e)
                }
            )

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up...")
        # Log environment variables (excluding sensitive ones)
        safe_vars = {k: v for k, v in os.environ.items() 
                    if not any(sensitive in k.lower() 
                             for sensitive in ['password', 'secret', 'key', 'token'])}
        logger.info(f"Environment variables: {safe_vars}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down...")

except Exception as e:
    error_message = str(e)
    logger.error(f"Application initialization error: {error_message}")
    app = FastAPI()
    
    # Mount static directory even in error case
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(os.path.join(static_dir, "favicon.png"))
    
    @app.get("/")
    async def root():
        return {
            "error": error_message,
            "message": "Failed to load main application"
        }
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "error", "error": error_message}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api.index:app", host="0.0.0.0", port=port, reload=True)

# This file is specifically for Vercel deployment
# It imports our FastAPI app from the main application file 