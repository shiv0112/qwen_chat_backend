import os
import json
import time
import httpx
import chainlit as cl

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8006/qwen3/chat")

# Hardcoded generation parameters
GENERATION_PARAMS = {
    "model": "qwen3",
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 2048,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "stream": True
}


@cl.on_chat_start
async def start_chat():
    cl.user_session.set("session_id", None)
    cl.user_session.set("locked", False)

    await cl.Message(
        content="Welcome !! Send your first message to get started !!"
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    # ❌ Reject file uploads explicitly
    if message.elements:
        await cl.Message(content="📁 File uploads are disabled for now.").send()
        return

    # Prepare payload
    payload = {
        "message": message.content,
        **GENERATION_PARAMS
    }

    session_id = cl.user_session.get("session_id")
    if session_id:
        payload["session_id"] = session_id

    start_time = time.time()
    thinking = False
    thinking_step = None
    final_answer = cl.Message(content="")  # Stream final reply here

    # Show temporary placeholder loader
    placeholder = cl.Message(content="⏳ AI is thinking...")
    await placeholder.send()

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(
                BACKEND_URL,
                json=payload,
                headers={"Accept": "text/event-stream"},
                timeout=None
            )

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue

                try:
                    json_data = json.loads(line[6:])
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON: {line}")
                    continue

                if json_data.get("type") == "session":
                    cl.user_session.set("session_id", json_data["session_id"])
                    cl.user_session.set("locked", True)
                    continue

                choices = json_data.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if not content:
                    continue

                # Enter thinking mode
                if content == "<think>":
                    thinking = True
                    # Remove loader
                    await placeholder.remove()
                    # Start streaming thinking step
                    thinking_step = cl.Step(name="🧠 AI is thinking...")
                    await thinking_step.__aenter__()
                    continue

                # Exit thinking mode
                if content == "</think>":
                    thinking = False
                    duration = round(time.time() - start_time)
                    thinking_step.name = f"🤔 AI Thought ({duration}s)"
                    await thinking_step.update()
                    await thinking_step.__aexit__(None, None, None)
                    continue

                # Stream into correct block
                if thinking and thinking_step:
                    await thinking_step.stream_token(content)
                else:
                    await final_answer.stream_token(content)

            await final_answer.send()

        except Exception as e:
            try:
                await placeholder.update(content=f"❌ Error: {e}")
            except Exception:
                await cl.Message(content=f"❌ Error: {e}").send()
