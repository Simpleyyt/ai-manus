from pydantic import BaseModel
from typing import Optional, List
from app.interfaces.schemas.event import AgentSSEEvent
from app.domain.models.file import FileInfo
from app.domain.models.session import SessionStatus, SessionSummary


class ChatAttachment(BaseModel):
    """File attachment reference in a chat request"""
    file_id: str
    filename: str

    def to_domain(self) -> FileInfo:
        return FileInfo(file_id=self.file_id, filename=self.filename)


class ChatRequest(BaseModel):
    """Chat request schema"""
    timestamp: Optional[int] = None
    message: Optional[str] = None
    attachments: Optional[List[ChatAttachment]] = None
    event_id: Optional[str] = None


class ShellViewRequest(BaseModel):
    """Shell view request schema"""
    session_id: str


class CreateSessionResponse(BaseModel):
    """Create session response schema"""
    session_id: str


class GetSessionResponse(BaseModel):
    """Get session response schema"""
    session_id: str
    title: Optional[str] = None
    status: SessionStatus
    events: List[AgentSSEEvent] = []
    is_shared: bool = False


class ListSessionItem(BaseModel):
    """List session item schema"""
    session_id: str
    title: Optional[str] = None
    latest_message: Optional[str] = None
    latest_message_at: Optional[int] = None
    status: SessionStatus
    unread_message_count: int
    is_shared: bool = False

    @staticmethod
    def from_domain(summary: SessionSummary) -> 'ListSessionItem':
        return ListSessionItem(
            session_id=summary.id,
            title=summary.title,
            status=summary.status,
            unread_message_count=summary.unread_message_count,
            latest_message=summary.latest_message,
            latest_message_at=int(summary.latest_message_at.timestamp()) if summary.latest_message_at else None,
            is_shared=summary.is_shared
        )


class ListSessionResponse(BaseModel):
    """List session response schema"""
    sessions: List[ListSessionItem]


class ConsoleRecord(BaseModel):
    """Console record schema"""
    ps1: str
    command: str
    output: str


class ShellViewResponse(BaseModel):
    """Shell view response schema"""
    output: str
    session_id: str
    console: Optional[List[ConsoleRecord]] = None


class ShareSessionResponse(BaseModel):
    """Share session response schema"""
    session_id: str
    is_shared: bool


class SharedSessionResponse(BaseModel):
    """Shared session response schema (for public access)"""
    session_id: str
    title: Optional[str] = None
    status: SessionStatus
    events: List[AgentSSEEvent] = []
    is_shared: bool
