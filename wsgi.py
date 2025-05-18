from api.index import app

# This file is for WSGI servers compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wsgi:app", host="0.0.0.0", port=8000, reload=True) 