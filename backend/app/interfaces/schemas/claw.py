from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.domain.models.claw import ClawStatus, ClawMessage, ClawAttachment


class ClawResponse(BaseModel):
    """Claw instance response schema"""
    id: str
    user_id: str
    status: ClawStatus
    container_name: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_claw(claw) -> 'ClawResponse':
        return ClawResponse(
            id=claw.id,
            user_id=claw.user_id,
            status=claw.status,
            container_name=claw.container_name,
            error_message=claw.error_message,
            expires_at=claw.expires_at,
            created_at=claw.created_at,
            updated_at=claw.updated_at,
        )


class ClawApiKeyResponse(BaseModel):
    """API key response schema"""
    api_key: str


class ClawChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    session_id: str = "default"


class ClawChatChunk(BaseModel):
    """Chat chunk event schema"""
    type: str
    content: Optional[str] = None
    stop_reason: Optional[str] = None
    error: Optional[str] = None


class ClawAttachmentSchema(BaseModel):
    """File attachment in a chat message"""
    file_id: str
    filename: str
    content_type: Optional[str] = None
    size: int = 0
    file_url: Optional[str] = None

    @staticmethod
    def from_domain(att: ClawAttachment) -> 'ClawAttachmentSchema':
        return ClawAttachmentSchema(
            file_id=att.file_id,
            filename=att.filename,
            content_type=att.content_type,
            size=att.size,
            file_url=att.file_url,
        )


class ClawMessageSchema(BaseModel):
    """A single chat message"""
    role: str
    content: str = ""
    timestamp: int
    attachments: Optional[List[ClawAttachmentSchema]] = None

    @staticmethod
    def from_domain(msg: ClawMessage) -> 'ClawMessageSchema':
        return ClawMessageSchema(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp,
            attachments=[ClawAttachmentSchema.from_domain(a) for a in msg.attachments] if msg.attachments else None,
        )


class ClawHistoryResponse(BaseModel):
    """Chat history response"""
    messages: List[ClawMessageSchema]
