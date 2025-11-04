from typing import Optional, Protocol, List
from datetime import datetime
from app.domain.models.session import Session, SessionStatus
from app.domain.models.file import FileInfo
from app.domain.models.event import BaseEvent

class SessionRepository(Protocol):
    """Repository interface for Session aggregate"""
    
    async def save(self, session: Session) -> None:
        """Save or update a session"""
        ...
    
    async def find_by_id(self, session_id: str) -> Optional[Session]:
        """Find a session by its ID"""
        ...
    
    async def find_by_user_id(self, user_id: str) -> List[Session]:
        """Find all sessions for a specific user"""
        ...
    
    async def find_by_id_and_user_id(self, session_id: str, user_id: str) -> Optional[Session]:
        """Find a session by ID and user ID (for authorization)"""
        ...
    
    async def update_title(self, session_id: str, title: str) -> None:
        """Update the title of a session"""
        ...

    async def update_latest_message(self, session_id: str, message: str, timestamp: datetime) -> None:
        """Update the latest message of a session"""
        ...

    async def add_event(self, session_id: str, event: BaseEvent) -> None:
        """Add an event to a session"""
        ...
    
    async def add_file(self, session_id: str, file_info: FileInfo) -> None:
        """Add a file to a session"""
        ...
    
    async def remove_file(self, session_id: str, file_id: str) -> None:
        """Remove a file from a session"""
        ...

    async def get_file_by_path(self, session_id: str, file_path: str) -> Optional[FileInfo]:
        """Get file by path from a session"""
        ...

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        """Update the status of a session"""
        ...
    
    async def update_unread_message_count(self, session_id: str, count: int) -> None:
        """Update the unread message count of a session"""
        ...
    
    async def increment_unread_message_count(self, session_id: str) -> None:
        """Increment the unread message count of a session"""
        ...
    
    async def decrement_unread_message_count(self, session_id: str) -> None:
        """Decrement the unread message count of a session"""
        ...
    
    async def update_shared_status(self, session_id: str, is_shared: bool) -> None:
        """Update the shared status of a session"""
        ...
    
    async def delete(self, session_id: str) -> None:
        """Delete a session"""
        ...
    
    async def get_all(self) -> List[Session]:
        """Get all sessions"""
        ...