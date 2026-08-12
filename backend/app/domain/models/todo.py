from enum import Enum

from pydantic import BaseModel


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoItem(BaseModel):
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
