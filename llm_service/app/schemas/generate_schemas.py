from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class GenRequest(BaseModel):
    messages: List[Dict[str, str]]
    stream: bool = False
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.95, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=0)
    max_tokens: int = Field(4096, gt=0)
    repetition_penalty: Optional[float] = Field(None, ge=1.0)
    stop: Optional[List[str]] = None

class GenChunk(BaseModel):
    token: str
