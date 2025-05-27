from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 50
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
