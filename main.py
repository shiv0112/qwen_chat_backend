# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
# from app.routers import chat

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="Qwen Chat Backend",
    description="FastAPI + Redis based LLM backend",
    version="1.0.0"
)

# Optional: Set allowed origins for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
# app.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Root route
@app.get("/")
def root():
    return {"message": "Qwen Chat Backend is running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)