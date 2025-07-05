# Pydantic data validation models will be defined here 

from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Represents a single message in a conversation."""
    
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion API, mirroring OpenAI API structure."""
    
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None 