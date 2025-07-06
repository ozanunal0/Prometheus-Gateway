from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class APIKey(SQLModel, table=True):
    __tablename__ = "api_keys"
    """
    Database model for API keys.
    
    This model stores hashed API keys with metadata for authentication
    and access control. The actual key is hashed for security.
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_key: str = Field(unique=True, index=True)
    owner: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False) 