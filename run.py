import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Use import string format
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload for development
    ) 