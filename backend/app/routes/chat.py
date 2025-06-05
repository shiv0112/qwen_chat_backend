import re
import json
import uuid
import httpx
import base64
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

from app.schemas.chat_schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatInitRequest, 
    ChatInitResponse,
    ImageRequest,
    ImageResponse
    )
from app.utils.session_store import get_session, save_session
from app.utils.prompt_builder import build_prompt
from app.config import (
    SYSTEM_PROMPT,
    TOKEN_PER_WORD,
    VLLM_ENDPOINT,
    IMAGE_GEN_URL
)

router = APIRouter()

@router.post("/chat/init", response_model=ChatInitResponse)
async def init_chat_mode(request: ChatInitRequest):
    mode = request.mode

    if mode not in ["image", "chat", "assistant"]:
        return JSONResponse(status_code=400, content={"error": "Invalid mode"})

    session_id = str(uuid.uuid4())

    session_data = {
        "tokens_used": 0,
        "mode": mode
    }

    save_session(session_id, session_data)
    return ChatInitResponse(session_id=session_id, mode=mode)

@router.post("/generate/image", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    session_id = request.session_id
    prompt = request.prompt

    if not prompt:
        return JSONResponse(status_code=400, content={"error": "Prompt is required"})
    
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "Session ID is required"})

    # Save session with mode
    session = get_session(session_id)

    sys_prompt = SYSTEM_PROMPT['image']
    messages = build_prompt(sys_prompt, [{"role": "user", "content": prompt}])

    vllm_payload = {
        "model": "./models",
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 5,
        "presence_penalty": 0.2,
        "frequency_penalty": 0.1,
        "max_tokens": 1024,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(VLLM_ENDPOINT, json=vllm_payload)
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]

    # print("QWEN REPLY\n", reply)
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
    # print("REPLY\n", reply)

    # Add user message to history for using later
    history = session.get("messages", [])
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": reply})
    save_session(session_id, {"messages": history})

    # Construct payload for image microservice
    payload = {
        "request_id": session_id,
        "prompt": reply,
        "num_inference_steps": request.num_inference_steps,
        "guidance_scale": request.guidance_scale,
        "max_sequence_length": request.max_sequence_length
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(IMAGE_GEN_URL, json=payload)
            resp.raise_for_status()
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    image_result = base64.b64encode(resp.content).decode("utf-8")

    return ImageResponse(
        session_id=session_id,
        prompt=prompt,
        image_result=image_result
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_message = request.message
    session_id = request.session_id

    if not user_message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})

    if not session_id:
        return JSONResponse(status_code=400, content={"error": "Session ID is required"})

    # Retrieve session
    session = get_session(session_id)
    history = session.get("messages", [])
    tokens_used = session.get("tokens_used", 0)
    mode = session.get("mode", "chat")

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Trim prompt
    prompt = SYSTEM_PROMPT[mode]
    messages = build_prompt(prompt, history)

    print(f"{'*' * 10} Prompt {'*' * 10} \n{messages}\n{'*' * 10} Prompt {'*' * 10}")

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
            approx_tokens = int(len(buffer.split()) * TOKEN_PER_WORD)
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
