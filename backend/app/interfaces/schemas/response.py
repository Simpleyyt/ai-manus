from typing import Any, Generic, Optional, TypeVar, List, Dict
from datetime import datetime
from pydantic import BaseModel
from app.interfaces.schemas.event import AgentSSEEvent
from app.domain.models.session import SessionStatus

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None 

    @staticmethod
    def success(data: Optional[T] = None) -> "APIResponse[T]":
        return APIResponse(code=0, msg="success", data=data)

    @staticmethod
    def error(code: int, msg: str) -> "APIResponse[T]":
        return APIResponse(code=code, msg=msg, data=None)


class CreateSessionResponse(BaseModel):
    session_id: str

class GetSessionResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    events: List[AgentSSEEvent] = []

class ListSessionItem(BaseModel):
    session_id: str
    title: Optional[str] = None
    latest_message: Optional[str] = None
    latest_message_at: Optional[int] = None
    status: SessionStatus
    unread_message_count: int

class ListSessionResponse(BaseModel):
    sessions: List[ListSessionItem]

class ConsoleRecord(BaseModel):
    ps1: str
    command: str
    output: str

class ShellViewResponse(BaseModel):
    output: str
    session_id: str
    console: Optional[List[ConsoleRecord]] = None

class FileViewResponse(BaseModel):
    content: str
    file: str

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    upload_date: str
    message: str


class FileInfoResponse(BaseModel):
    file_id: str
    filename: str
    content_type: Optional[str]
    size: int
    upload_date: str
    metadata: Optional[Dict[str, Any]]
