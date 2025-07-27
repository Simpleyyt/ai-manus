from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    timestamp: Optional[int] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    event_id: Optional[str] = None

class FileViewRequest(BaseModel):
    file: str

class ShellViewRequest(BaseModel):
    session_id: str

class AccessTokenRequest(BaseModel):
    expire_minutes: int = Field(15, description="Token expiration time in minutes (max 15 minutes)", ge=1, le=15)
