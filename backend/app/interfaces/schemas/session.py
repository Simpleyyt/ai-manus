from pydantic import BaseModel
from typing import Optional, List
from app.interfaces.schemas.event import AgentSSEEvent
from app.domain.models.session import SessionStatus, SessionSummary, TaskMode


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
    is_favorite: bool = False
    is_pinned: bool = False
    project_id: Optional[str] = None
    task_mode: TaskMode = TaskMode.AGENT


class ListSessionItem(BaseModel):
    """List session item schema"""
    session_id: str
    title: Optional[str] = None
    latest_message: Optional[str] = None
    latest_message_at: Optional[int] = None
    status: SessionStatus
    unread_message_count: int
    is_shared: bool = False
    is_favorite: bool = False
    is_pinned: bool = False
    project_id: Optional[str] = None
    task_mode: TaskMode = TaskMode.AGENT

    @staticmethod
    def from_domain(summary: SessionSummary) -> 'ListSessionItem':
        return ListSessionItem(
            session_id=summary.id,
            title=summary.title,
            status=summary.status,
            unread_message_count=summary.unread_message_count,
            latest_message=summary.latest_message,
            latest_message_at=int(summary.latest_message_at.timestamp()) if summary.latest_message_at else None,
            is_shared=summary.is_shared,
            is_favorite=summary.is_favorite,
            is_pinned=summary.is_pinned,
            project_id=summary.project_id,
            task_mode=summary.task_mode or TaskMode.AGENT,
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


class UpdateSessionTitleRequest(BaseModel):
    """Update session title request schema"""
    title: str


class UpdateSessionTitleResponse(BaseModel):
    """Update session title response schema"""
    session_id: str
    title: str


class FavoriteSessionResponse(BaseModel):
    """Favorite session response schema"""
    session_id: str
    is_favorite: bool


class PinSessionRequest(BaseModel):
    """Pin / unpin session"""
    is_pinned: bool = True


class PinSessionResponse(BaseModel):
    """Pin session response schema"""
    session_id: str
    is_pinned: bool


class FavoriteLibraryFileResponse(BaseModel):
    """Favorite library file response schema"""
    file_id: str
    is_favorite: bool


class MoveSessionProjectRequest(BaseModel):
    """Move session to project (null to remove from project)"""
    project_id: Optional[str] = None


class MoveSessionProjectResponse(BaseModel):
    session_id: str
    project_id: Optional[str] = None


class UpdateSessionTaskModeRequest(BaseModel):
    """Update session task mode (agent | chat)"""
    task_mode: TaskMode


class UpdateSessionTaskModeResponse(BaseModel):
    session_id: str
    task_mode: TaskMode


class LibraryFileItem(BaseModel):
    session_id: str
    session_title: Optional[str] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    upload_date: Optional[str] = None
    is_favorite: bool = False
    latest_message_at: Optional[int] = None


class LibraryResponse(BaseModel):
    files: List[LibraryFileItem]


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
