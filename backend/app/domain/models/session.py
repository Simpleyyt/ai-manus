from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import List, Optional
from enum import Enum
import uuid
from app.domain.models.event import PlanEvent, AgentEvent
from app.domain.models.plan import Plan
from app.domain.models.file import FileInfo


class SessionStatus(str, Enum):
    """Session status enum"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"


class Session(BaseModel):
    """Session model"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str  # User ID that owns this session
    sandbox_id: Optional[str] = Field(default=None)  # Identifier for the sandbox environment
    agent_id: str
    task_id: Optional[str] = None
    title: Optional[str] = None
    unread_message_count: int = 0
    latest_message: Optional[str] = None
    latest_message_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    events: List[AgentEvent] = []
    files: List[FileInfo] = []
    status: SessionStatus = SessionStatus.PENDING
    is_shared: bool = False  # Whether this session is shared publicly

    def get_last_plan(self) -> Optional[Plan]:
        """Get the last plan from the events"""
        for event in reversed(self.events):
            if isinstance(event, PlanEvent):
                return event.plan
        return None