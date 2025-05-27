# app/routers/chat.py

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat, stream_chat

router = APIRouter()

@router.post("/", response_model=ChatResponse, response_model_exclude_none=True)
async def chat_endpoint(req: ChatRequest):
    """
    Handles user chat requests and returns assistant response.
    Supports streaming and non-streaming modes.
    """
    if req.stream:
        async def token_stream():
            async for chunk in stream_chat(req):
                yield chunk.json() + "\n"

        return StreamingResponse(token_stream(), media_type="application/jsonlines")

    else:
        response = await handle_chat(req)
        return JSONResponse(content=response.dict())
