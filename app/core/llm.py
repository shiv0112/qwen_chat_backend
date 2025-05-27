# app/core/llm.py

import httpx
import os
from typing import List, Dict, AsyncGenerator
from app.schemas.chat_schema import ChatChunk

VLLM_GENERATE_URL = os.getenv("VLLM_GENERATE_URL", "http://localhost:8000/generate")

# Optional: Use stop sequence or max_tokens defaults if needed
DEFAULT_STOP = ["<|im_end|>"]
DEFAULT_MAX_TOKENS = 1024

async def get_completion(messages: List[Dict[str, str]]) -> str:
    """
    Call the local vLLM server for full-text generation (non-streaming).
    """
    payload = {
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "stop": DEFAULT_STOP
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(VLLM_GENERATE_URL, json=payload)
        response.raise_for_status()
        return response.json()["text"]

async def stream_completion(messages: List[Dict[str, str]]) -> AsyncGenerator[ChatChunk, None]:
    """
    Call the local vLLM server for streaming generation.
    Yields ChatChunk objects one token at a time.
    """
    payload = {
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "stop": DEFAULT_STOP
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", VLLM_GENERATE_URL, json=payload) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = ChatChunk.parse_raw(line)
                    yield data
                except Exception:
                    continue
