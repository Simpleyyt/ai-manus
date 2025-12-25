from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Step(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    success: bool = False
    attachments: List[str] = []
    reflection: Optional[str] = None  # Self-reflection on failure or unexpected results

    def is_done(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED or self.status == ExecutionStatus.FAILED

class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    goal: str = ""
    language: Optional[str] = "en"
    steps: List[Step] = []
    message: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def is_done(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED or self.status == ExecutionStatus.FAILED
    
    def get_next_step(self) -> Optional[Step]:
        for step in self.steps:
            if not step.is_done():
                return step
        return None
    
    def dump_json(self) -> str:
        return self.model_dump_json(include={"goal", "language", "steps"})
