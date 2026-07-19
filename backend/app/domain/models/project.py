from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Optional
import uuid


class Project(BaseModel):
    """Project workspace for grouping sessions"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str
    name: str
    instruction: Optional[str] = None
    is_pinned: bool = False
    sort_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
