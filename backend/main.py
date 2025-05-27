from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, sessions

app = FastAPI(title="Fuckwad AI Backend", version="1.0")

# CORS setup – modify as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(sessions.router, prefix="/sessions", tags=["Session"])

# Optional: TTL cleanup or model warmup on startup
@app.on_event("startup")
async def on_startup():
    print("🔥 Server is starting...")
    from app.utils.session_store import cleanup_expired_sessions
    cleanup_expired_sessions()

@app.on_event("shutdown")
async def on_shutdown():
    print("🧼 Server is shutting down. Cleaning up...")
    from app.utils.session_store import cleanup_expired_sessions
    cleanup_expired_sessions()
