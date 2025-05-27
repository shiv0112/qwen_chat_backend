import json
import uuid
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

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

@router.post("/chat")
async def chat(request: Request):
    payload = await request.json()

    user_message = payload.get("message")
    session_id = payload.get("session_id", str(uuid.uuid4()))
    temperature = payload.get("temperature", TEMPERATURE)
    max_tokens = payload.get("max_tokens", MAX_TOKENS)
    top_p = payload.get("top_p", TOP_P)
    top_k = payload.get("top_k", TOP_K)
    presence_penalty = payload.get("presence_penalty", PRESENCE_PENALTY)
    frequency_penalty = payload.get("frequency_penalty", FREQUENCY_PENALTY)
    stream = payload.get("stream", False)

    if not user_message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})

    # Get session
    session = get_session(session_id)
    history = session.get("messages", [])
    tokens_used = session.get("tokens_used", 0)

    # Update user message
    history.append({"role": "user", "content": user_message})

    # Build trimmed prompt
    messages = build_prompt(SYSTEM_PROMPT, history, MAX_CONTEXT_LENGTH, max_tokens)

    # Prepare payload
    vllm_payload = {
        "model": "./models",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "top_k": top_k,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "stream": stream
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        if stream:
            async def stream_response():
                buffer = ""
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

                # Approximate tokens and save assistant response
                approx_tokens = int(len(buffer.split()) * 1.3)
                history.append({"role": "assistant", "content": buffer})
                tokens_used += approx_tokens
                save_session(session_id, {"messages": history, "tokens_used": tokens_used})

            # Save user message early
            save_session(session_id, {"messages": history, "tokens_used": tokens_used})
            return StreamingResponse(stream_response(), media_type="text/event-stream")

        else:
            resp = await client.post(VLLM_ENDPOINT, json=vllm_payload)
            data = resp.json()

            reply = data["choices"][0]["message"]["content"]
            used = data.get("usage", {}).get("total_tokens", 0)

            history.append({"role": "assistant", "content": reply})
            tokens_used += used
            save_session(session_id, {"messages": history, "tokens_used": tokens_used})

            return {
                "session_id": session_id,
                "reply": reply,
                "tokens_used": tokens_used
            }

@router.delete("/chat/{session_id}")
def delete_chat_session(session_id: str):
    delete_session(session_id)
    return {"message": f"Session {session_id} deleted successfully."}
