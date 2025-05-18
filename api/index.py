from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import sys
import os
import psycopg2
import sqlalchemy.exc

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
        return FileResponse(os.path.join(static_dir, "favicon.ico"))
    
    @app.get("/api/healthcheck")
    async def healthcheck():
        return {"status": "ok"}

    @app.middleware("http")
    async def db_session_middleware(request, call_next):
        try:
            response = await call_next(request)
            return response
        except (psycopg2.OperationalError, sqlalchemy.exc.OperationalError) as e:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Database connection error. Please try again later.",
                    "detail": str(e)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "An unexpected error occurred.",
                    "detail": str(e)
                }
            )

except Exception as e:
    error_message = str(e)
    app = FastAPI()
    
    # Mount static directory even in error case
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(os.path.join(static_dir, "favicon.ico"))
    
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