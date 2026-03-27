from typing import Optional, List
from datetime import datetime, UTC
from pydantic import BaseModel, Field
from enum import Enum


class ClawAttachment(BaseModel):
    """File attachment within a Claw chat message"""
    file_id: str
    filename: str
    content_type: Optional[str] = None
    size: int = 0
    file_url: Optional[str] = None


class ClawMessage(BaseModel):
    """A single chat message in a Claw conversation"""
    role: str  # 'user' | 'assistant' | 'attachments'
    content: str = ""
    timestamp: int  # Unix timestamp (seconds)
    attachments: Optional[List[ClawAttachment]] = None


class ClawStatus(str, Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class Claw(BaseModel):
    """Claw domain model - represents a user's OpenClaw instance"""
    id: str
    user_id: str
    container_name: Optional[str] = None
    container_ip: Optional[str] = None
    api_key: str  # Per-user OpenAI-compatible API key for LLM proxy
    status: ClawStatus = ClawStatus.CREATING
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def http_base_url(self) -> Optional[str]:
        """HTTP base URL for the manus-claw plugin server"""
        if self.container_ip:
            return f"http://{self.container_ip}:18788"
        return None
