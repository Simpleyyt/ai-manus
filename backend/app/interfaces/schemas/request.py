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
