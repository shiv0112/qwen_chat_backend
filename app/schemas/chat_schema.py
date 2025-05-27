# app/schemas/chat_schema.py

from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        None, description="Client session ID. If not provided, backend will generate one."
    )
    message: str = Field(..., description="User's message to the assistant.")
    stream: bool = Field(
        False, description="Whether to stream the response token-by-token."
    )

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Session ID used for this interaction.")
    response: str = Field(..., description="Full assistant response.")

class ChatChunk(BaseModel):
    token: str = Field(..., description="A single token from the assistant stream.")
