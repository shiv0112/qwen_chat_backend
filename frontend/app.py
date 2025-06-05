import os
import json
import httpx
import base64
import chainlit as cl

BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8006")

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
    """Initialize chat session and prompt user to select mode"""
    cl.user_session.set("session_id", None)
    cl.user_session.set("mode", None)
    cl.user_session.set("locked", False)

    await cl.Message(
        content="🤖 **Welcome to the Multi-Mode AI Assistant!**\n\nPlease choose a mode to begin:",
        actions=[
            cl.Action(name="set_mode", value="chat", label="💬 Chat", payload={"mode": "chat"}),
            cl.Action(name="set_mode", value="assistant", label="🧠 Assistant", payload={"mode": "assistant"}),
            cl.Action(name="set_mode", value="image", label="🎨 Image Generator", payload={"mode": "image"})
        ]
    ).send()

@cl.action_callback("set_mode")
async def on_action(action):
    """Handle mode selection from action buttons"""
    mode = action.payload.get("mode") if action.payload else action.value
    await set_mode(mode)

async def set_mode(mode):
    """Set the mode and initialize backend session"""
    if mode not in ["chat", "assistant", "image"]:
        await cl.Message(content="❌ Invalid mode. Please choose from the available options.").send()
        return

    cl.user_session.set("mode", mode)

    try:
        # Initialize chat session with backend
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_BASE_URL}/qwen3/chat/init", 
                json={"mode": mode}
            )
            resp.raise_for_status()
            session_data = resp.json()
            session_id = session_data.get("session_id")
            
            if not session_id:
                raise ValueError("No session_id returned from backend")
                
            cl.user_session.set("session_id", session_id)

        mode_descriptions = {
            "chat": "💬 **Chat Mode** - Casual conversation with the AI",
            "assistant": "🧠 **Assistant Mode** - Advanced AI assistance with reasoning steps",
            "image": "🎨 **Image Generator Mode** - Create images from text descriptions"
        }

        await cl.Message(
            content=f"✅ {mode_descriptions[mode]}\n\nYou can now start chatting! Type your message below."
        ).send()

    except httpx.RequestError as e:
        await cl.Message(
            content=f"❌ **Connection Error**: Could not connect to backend server.\n```\n{str(e)}\n```"
        ).send()
    except httpx.HTTPStatusError as e:
        await cl.Message(
            content=f"❌ **Backend Error**: Server returned status {e.response.status_code}\n```\n{str(e)}\n```"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ **Initialization Error**: {str(e)}"
        ).send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming messages based on current mode"""
    mode = cl.user_session.get("mode")
    session_id = cl.user_session.get("session_id")

    # Handle mode selection if not set
    if not mode:
        user_input = message.content.lower().strip()
        mode_mapping = {
            "chat": "chat",
            "assistant": "assistant", 
            "image": "image",
            "1": "chat",
            "2": "assistant",
            "3": "image"
        }
        
        if user_input in mode_mapping:
            await set_mode(mode_mapping[user_input])
        else:
            await cl.Message(
                content="❌ Please select a valid mode using the buttons above or type:\n- `chat` for Chat Mode\n- `assistant` for Assistant Mode\n- `image` for Image Generator Mode"
            ).send()
        return

    if not session_id:
        await cl.Message(content="❌ Session not initialized. Please refresh the page.").send()
        return

    # Check if user is locked (processing previous request)
    if cl.user_session.get("locked", False):
        await cl.Message(content="⏳ Please wait for the current request to complete.").send()
        return

    user_input = message.content.strip()
    if not user_input:
        await cl.Message(content="❌ Please enter a valid message.").send()
        return

    # Lock session to prevent concurrent requests
    cl.user_session.set("locked", True)

    try:
        if mode in ["chat", "assistant"]:
            await handle_chat(user_input, session_id)
        elif mode == "image":
            await handle_image_generation(user_input, session_id)
    finally:
        # Always unlock session
        cl.user_session.set("locked", False)

async def handle_chat(user_input, session_id):
    """Handle chat and assistant modes with streaming response"""
    payload = {
        "message": user_input,
        "session_id": session_id,
        **GENERATION_PARAMS
    }

    final_answer = cl.Message(content="")
    placeholder = cl.Message(content="⏳ AI reasoning ...")
    await placeholder.send()

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(
                f"{BACKEND_BASE_URL}/qwen3/chat",
                json=payload,
                headers={"Accept": "text/event-stream"},
                timeout=None
            )
            response.raise_for_status()

            thinking = False
            thinking_step = None
            content_received = False

            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                
                try:
                    json_data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                if json_data.get("type") == "session":
                    continue

                delta = json_data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                
                if not content:
                    continue

                content_received = True

                if content == "<think>":
                    await placeholder.remove()
                    thinking_step = cl.Step(name="🧠 AI reasoning ...")
                    await thinking_step.__aenter__()
                    thinking = True
                    continue

                if content == "</think>":
                    thinking = False
                    if thinking_step:
                        await thinking_step.__aexit__(None, None, None)
                        thinking_step = None
                    continue

                if thinking and thinking_step:
                    await thinking_step.stream_token(content)
                else:
                    if placeholder:
                        await placeholder.remove()
                        placeholder = None
                    await final_answer.stream_token(content)

            # Clean up if no content was received
            if not content_received:
                await placeholder.remove()
                await cl.Message(content="❌ No response received from the AI.").send()
            else:
                if placeholder:
                    await placeholder.remove()
                await final_answer.send()

        except httpx.RequestError as e:
            await placeholder.remove()
            await cl.Message(content=f"❌ **Connection Error**: {str(e)}").send()
        except httpx.HTTPStatusError as e:
            await placeholder.remove()
            await cl.Message(content=f"❌ **Server Error**: {e.response.status_code} - {str(e)}").send()
        except Exception as e:
            await placeholder.remove()
            await cl.Message(content=f"❌ **Error**: {str(e)}").send()

async def handle_image_generation(prompt, session_id):
    """Handle image generation requests"""
    image_payload = {
        "session_id": session_id,
        "prompt": prompt,
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
        "max_sequence_length": 512
    }

    # Show generation status
    status_msg = cl.Message(content="🎨 **Generating image...** This may take a few moments.")
    await status_msg.send()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{BACKEND_BASE_URL}/qwen3/generate/image", 
                json=image_payload
            )
            resp.raise_for_status()
            
            data = resp.json()
            b64_image = data.get("image_result")
            
            await status_msg.remove()
            
            if b64_image:
                raw_image_bytes = base64.b64decode(data.get("image_result"))
                await cl.Message(
                    content=f"🖼️ **Generated Image**\n\n*",
                    elements=[
                        cl.Image(
                            name="generated_image.png", 
                            display="inline", 
                            content=raw_image_bytes
                        )
                    ]
                ).send()
            else:
                await cl.Message(content="⚠️ **Warning**: No image data returned from the server.").send()
                
                
        except httpx.TimeoutException:
            await status_msg.remove()
            await cl.Message(content="❌ **Timeout Error**: Image generation took too long. Please try again with a simpler prompt.").send()
        except httpx.RequestError as e:
            await status_msg.remove()
            await cl.Message(content=f"❌ **Connection Error**: Could not connect to image generation service.\n```\n{str(e)}\n```").send()
        except httpx.HTTPStatusError as e:
            await status_msg.remove()
            await cl.Message(content=f"❌ **Image Generation Error**: Server returned status {e.response.status_code}\n```\n{str(e)}\n```").send()
        except Exception as e:
            await status_msg.remove()
            await cl.Message(content=f"❌ **Unexpected Error**: {str(e)}").send()

# Note: File upload handling removed due to version compatibility
# If your Chainlit version supports it, you can add:
# @cl.on_file_upload
# async def handle_file_upload(files):
#     await cl.Message(content="🚫 File uploads are not supported.").send()
#     return []