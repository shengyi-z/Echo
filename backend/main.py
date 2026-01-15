import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Check if API key is loaded
api_key = os.getenv("BACKBOARD_API_KEY")

from .api import chat, goals, plans, tasks

# App instance and global middleware.
app = FastAPI(title="Echo API")

# Enable CORS for frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers.
app.include_router(chat.router)
app.include_router(goals.router)
app.include_router(plans.router)
app.include_router(tasks.router)

# Basic health check.


@app.get("/")
def read_root():
    return {"message": "Echo API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
