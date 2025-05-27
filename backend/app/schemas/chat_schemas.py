# app/schemas/chat_schemas.py

from pydantic import BaseModel
from typing import Optional
from app.config import (
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    TOP_K,
    PRESENCE_PENALTY,
    FREQUENCY_PENALTY
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    temperature: Optional[float] = TEMPERATURE
    max_tokens: Optional[int] = MAX_TOKENS
    top_p: Optional[float] = TOP_P
    top_k: Optional[int] = TOP_K
    presence_penalty: Optional[float] = PRESENCE_PENALTY
    frequency_penalty: Optional[float] = FREQUENCY_PENALTY
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tokens_used: Optional[int]
