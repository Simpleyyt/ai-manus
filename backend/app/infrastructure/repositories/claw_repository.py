from typing import Optional, List
from datetime import datetime, UTC
from app.infrastructure.models.documents import ClawDocument
from app.domain.models.claw import Claw, ClawMessage, ClawAttachment
import logging

logger = logging.getLogger(__name__)


class ClawRepository:
    """MongoDB repository for Claw instances"""

    async def get_by_user_id(self, user_id: str) -> Optional[Claw]:
        """Get claw instance by user ID"""
        doc = await ClawDocument.find_one(ClawDocument.user_id == user_id)
        if not doc:
            return None
        return doc.to_domain()

    async def get_by_id(self, claw_id: str) -> Optional[Claw]:
        """Get claw instance by claw ID"""
        doc = await ClawDocument.find_one(ClawDocument.claw_id == claw_id)
        if not doc:
            return None
        return doc.to_domain()

    async def get_by_api_key(self, api_key: str) -> Optional[Claw]:
        """Get claw instance by API key"""
        doc = await ClawDocument.find_one(ClawDocument.api_key == api_key)
        if not doc:
            return None
        return doc.to_domain()

    async def create(self, claw: Claw) -> Claw:
        """Create a new claw instance"""
        doc = ClawDocument.from_domain(claw)
        await doc.insert()
        return doc.to_domain()

    async def update(self, claw: Claw) -> Claw:
        """Update an existing claw instance"""
        doc = await ClawDocument.find_one(ClawDocument.claw_id == claw.id)
        if not doc:
            raise ValueError(f"Claw not found: {claw.id}")
        doc.update_from_domain(claw)
        await doc.save()
        return doc.to_domain()

    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete claw instance by user ID"""
        doc = await ClawDocument.find_one(ClawDocument.user_id == user_id)
        if not doc:
            return False
        await doc.delete()
        return True

    async def get_messages(self, user_id: str) -> List[ClawMessage]:
        """Get chat message history for a user's claw"""
        doc = await ClawDocument.find_one(ClawDocument.user_id == user_id)
        if not doc:
            return []
        return doc.messages

    async def append_message(
        self, user_id: str, role: str, content: str = "",
        attachments: Optional[List[ClawAttachment]] = None,
    ) -> None:
        """Append a message to the claw's chat history"""
        doc = await ClawDocument.find_one(ClawDocument.user_id == user_id)
        if not doc:
            return
        msg = ClawMessage(
            role=role,
            content=content,
            timestamp=int(datetime.now(UTC).timestamp()),
            attachments=attachments,
        )
        doc.messages.append(msg)
        doc.updated_at = datetime.now(UTC)
        await doc.save()

    async def clear_messages(self, user_id: str) -> None:
        """Clear all chat messages for a user's claw"""
        doc = await ClawDocument.find_one(ClawDocument.user_id == user_id)
        if not doc:
            return
        doc.messages = []
        doc.updated_at = datetime.now(UTC)
        await doc.save()
