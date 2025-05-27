from fastapi import FastAPI
from app.routers import generate

app = FastAPI(
    title="Qwen (vLLM) AI Service",
    description="Streaming/non-streaming generation endpoint with custom system prompt.",
)

app.include_router(generate.router)

@app.get("/")
def root():
    return {
        "message": "LLM service is running! System prompt injected.",
    }