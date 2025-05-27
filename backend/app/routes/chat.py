import uuid
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.session import get_session, save_session
from app.utils.prompt_utils import build_prompt
from app.config import SYSTEM_PROMPT, MAX_CONTEXT_LENGTH, MAX_TOKENS, VLLM_ENDPOINT

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    payload = await request.json()

    user_message = payload.get("message")
    session_id = payload.get("session_id", str(uuid.uuid4()))
    temperature = payload.get("temperature", 0.7)
    max_tokens = payload.get("max_tokens", MAX_TOKENS)
    top_p = payload.get("top_p", 0.9)
    presence_penalty = payload.get("presence_penalty", 0.2)
    frequency_penalty = payload.get("frequency_penalty", 0.1)
    stream = payload.get("stream", False)

    if not user_message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})

    # Retrieve and update session
    history = get_session(session_id)
    history.append({"role": "user", "content": user_message})

    # Trim prompt to fit context window
    messages = build_prompt(SYSTEM_PROMPT, history, MAX_CONTEXT_LENGTH, max_tokens)

    vllm_payload = {
        "model": "./models",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "stream": stream
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        if stream:
            async def stream_response():
                async with client.stream("POST", VLLM_ENDPOINT, json=vllm_payload) as response:
                    async for line in response.aiter_lines():
                        if line.strip().startswith("data: "):
                            yield line.strip() + "\n"

            # Save user message only; assistant message will not be known until stream ends
            save_session(session_id, history)
            return StreamingResponse(stream_response(), media_type="text/event-stream")

        else:
            resp = await client.post(VLLM_ENDPOINT, json=vllm_payload)
            data = resp.json()

            reply = data["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": reply})
            save_session(session_id, history)

            return {
                "session_id": session_id,
                "reply": reply,
                "tokens_used": data.get("usage", {}).get("total_tokens")
            }
