# app/services/chat_service.py

from typing import AsyncGenerator
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatChunk
from app.core.redis_store import (
    generate_session_id,
    create_session_if_missing,
    get_chat_history,
    save_message
)
from app.core.llm import build_messages, get_completion, stream_completion

async def handle_chat(req: ChatRequest) -> ChatResponse:
    """
    Handles a complete chat cycle (non-streaming).
    """
    # 1. Ensure session_id
    session_id = req.session_id or generate_session_id()
    create_session_if_missing(session_id)

    # 2. Get history and build prompt
    history = get_chat_history(session_id)
    messages = build_messages(history, req.message)

    # 3. Get LLM response
    assistant_reply = await get_completion(messages)

    # 4. Save chat in Redis
    save_message(session_id, "user", req.message)
    save_message(session_id, "assistant", assistant_reply)

    # 5. Return response
    return ChatResponse(session_id=session_id, response=assistant_reply)

async def stream_chat(req: ChatRequest) -> AsyncGenerator[ChatChunk, None]:
    """
    Handles a streaming chat response, token by token.
    """
    session_id = req.session_id or generate_session_id()
    create_session_if_missing(session_id)

    history = get_chat_history(session_id)
    messages = build_messages(history, req.message)

    # Save user message early
    save_message(session_id, "user", req.message)

    # Stream each token
    full_response = ""

    async for chunk in stream_completion(messages):
        full_response += chunk.token
        yield chunk

    # Save full assistant reply at the end
    save_message(session_id, "assistant", full_response)
