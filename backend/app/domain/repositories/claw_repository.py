from typing import Optional, List, Protocol

from app.domain.models.claw import Claw, ClawMessage, ClawAttachment


class ClawRepository(Protocol):
    """Repository interface for Claw aggregate"""

    async def get_by_user_id(self, user_id: str) -> Optional[Claw]:
        """Get claw instance by user ID"""
        ...

    async def get_by_id(self, claw_id: str) -> Optional[Claw]:
        """Get claw instance by claw ID"""
        ...

    async def get_by_api_key(self, api_key: str) -> Optional[Claw]:
        """Get claw instance by API key"""
        ...

    async def create(self, claw: Claw) -> Claw:
        """Create a new claw instance"""
        ...

    async def update(self, claw: Claw) -> Claw:
        """Update an existing claw instance"""
        ...

    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete claw instance by user ID"""
        ...

    async def get_messages(self, user_id: str) -> List[ClawMessage]:
        """Get chat message history for a user's claw"""
        ...

    async def append_message(
        self, user_id: str, role: str, content: str = "",
        attachments: Optional[List[ClawAttachment]] = None,
    ) -> None:
        """Append a message to the claw's chat history"""
        ...

    async def clear_messages(self, user_id: str) -> None:
        """Clear all chat messages for a user's claw"""
        ...
