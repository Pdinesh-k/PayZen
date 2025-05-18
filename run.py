from app.main import app
from app import models
from app.database import engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

# This is used by Vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True) 