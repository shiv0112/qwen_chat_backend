import json
import uuid
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.utils.session_store import delete_session, get_session, save_session
from app.utils.prompt_builder import build_prompt
from app.config import (
    SYSTEM_PROMPT,
    MAX_CONTEXT_LENGTH,
    MAX_TOKENS,
    VLLM_ENDPOINT,
    TEMPERATURE,
    TOP_P,
    TOP_K,
    PRESENCE_PENALTY,
    FREQUENCY_PENALTY
)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_message = request.message
    session_id = request.session_id or str(uuid.uuid4())

    if not user_message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})

    # Retrieve session
    session = get_session(session_id)
    history = session.get("messages", [])
    tokens_used = session.get("tokens_used", 0)

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Trim prompt
    messages = build_prompt(SYSTEM_PROMPT, history, MAX_CONTEXT_LENGTH, request.max_tokens)

    # Build payload
    vllm_payload = {
        "model": "./models",
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
        "top_k": request.top_k,
        "presence_penalty": request.presence_penalty,
        "frequency_penalty": request.frequency_penalty,
        "stream": request.stream
    }

    if request.stream:
        # Save user message before streaming
        save_session(session_id, {"messages": history, "tokens_used": tokens_used})

        async def stream_response(history_snapshot, tokens_snapshot):
            buffer = ""

            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", VLLM_ENDPOINT, json=vllm_payload) as response:
                    async for line in response.aiter_lines():
                        if line.strip().startswith("data: "):
                            json_str = line.strip().removeprefix("data: ").strip()
                            if json_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(json_str)
                                content_piece = chunk["choices"][0]["delta"].get("content", "")
                                buffer += content_piece
                            except Exception:
                                pass
                            yield line.strip() + "\n"
            yield "data: [DONE]\n"

            # Save assistant response after streaming completes
            approx_tokens = int(len(buffer.split()) * 1.3)
            history_snapshot.append({"role": "assistant", "content": buffer})
            tokens_snapshot += approx_tokens
            save_session(session_id, {"messages": history_snapshot, "tokens_used": tokens_snapshot})

        return StreamingResponse(stream_response(history.copy(), tokens_used), media_type="text/event-stream")

    else:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(VLLM_ENDPOINT, json=vllm_payload)
            data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        used = data.get("usage", {}).get("total_tokens", 0)

        history.append({"role": "assistant", "content": reply})
        tokens_used += used
        save_session(session_id, {"messages": history, "tokens_used": tokens_used})

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            tokens_used=tokens_used
        )
