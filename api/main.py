from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PayZen API is running"}

@app.get("/debug")
async def debug():
    return {
        "environment": dict(os.environ),
        "database_url": os.getenv("DATABASE_URL", "not set"),
        "python_path": os.getenv("PYTHONPATH", "not set")
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": str(exc),
            "type": str(type(exc).__name__)
        }
    ) 