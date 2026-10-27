import uvicorn
import os
import sys

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.config import settings

if __name__ == "__main__":
    print(f"Starting Music Recommender Backend on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
