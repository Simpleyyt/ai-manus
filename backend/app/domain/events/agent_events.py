from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Optional, Union, List
from datetime import datetime
import time
import uuid
from enum import Enum
from app.domain.models.plan import Plan, Step


class PlanStatus(str, Enum):
    """Plan status enum"""
    CREATED = "created"
    UPDATED = "updated"
    COMPLETED = "completed"


class StepStatus(str, Enum):
    """Step status enum"""
    STARTED = "started"
    FAILED = "failed"
    COMPLETED = "completed"


class ToolStatus(str, Enum):
    """Tool status enum"""
    CALLING = "calling"
    CALLED = "called"


class BaseEvent(BaseModel):
    """Base class for agent events"""
    type: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class ErrorEvent(BaseEvent):
    """Error event"""
    type: Literal["error"] = "error"
    error: str

class PlanEvent(BaseEvent):
    """Plan related events"""
    type: Literal["plan"] = "plan"
    plan: Plan
    status: PlanStatus
    step: Optional[Step] = None

class BrowserToolContent(BaseModel):
    """Browser tool content"""
    screenshot: str

class SearchToolContent(BaseModel):
    """Search tool content"""
    results: List[Dict[str, Any]]

class ShellToolContent(BaseModel):
    """Shell tool content"""
    console: Any

class FileToolContent(BaseModel):
    """File tool content"""
    content: str

ToolContent = Union[BrowserToolContent, SearchToolContent, ShellToolContent, FileToolContent]

class ToolEvent(BaseEvent):
    """Tool related events"""
    type: Literal["tool"] = "tool"
    tool_call_id: str
    tool_name: str
    tool_content: Optional[ToolContent] = None
    function_name: str
    function_args: Dict[str, Any]
    status: ToolStatus
    function_result: Optional[Any] = None

class TitleEvent(BaseEvent):
    """Title event"""
    type: Literal["title"] = "title"
    title: str

class StepEvent(BaseEvent):
    """Step related events"""
    type: Literal["step"] = "step"
    step: Step
    status: StepStatus

class MessageEvent(BaseEvent):
    """Message event"""
    type: Literal["message"] = "message"
    role: Literal["user", "assistant"] = "assistant"
    message: str

class DoneEvent(BaseEvent):
    """Done event"""
    type: Literal["done"] = "done"

class WaitEvent(BaseEvent):
    """Wait event"""
    type: Literal["wait"] = "wait"

AgentEvent = Union[
    BaseEvent,
    ErrorEvent,
    PlanEvent, 
    ToolEvent,
    StepEvent,
    MessageEvent,
    DoneEvent,
    TitleEvent,
    WaitEvent
]


class AgentEventFactory:
    """Factory class for JSON conversion and AgentEvent manipulation"""
    
    @staticmethod
    def from_json(event_str: str) -> AgentEvent:
        """Create an AgentEvent from JSON string"""
        event = BaseEvent.model_validate_json(event_str)
        
        if (event.type == "plan"):
            return PlanEvent.model_validate_json(event_str)
        elif (event.type == "step"): 
            return StepEvent.model_validate_json(event_str)
        elif (event.type == "tool"):
            return ToolEvent.model_validate_json(event_str)
        elif (event.type == "message"):
            return MessageEvent.model_validate_json(event_str)
        elif (event.type == "error"):
            return ErrorEvent.model_validate_json(event_str)
        elif (event.type == "done"):
            return DoneEvent.model_validate_json(event_str)
        elif (event.type == "title"):
            return TitleEvent.model_validate_json(event_str)
        elif (event.type == "wait"):
            return WaitEvent.model_validate_json(event_str)
        else:
            return event
    
    @staticmethod
    def to_json(event: AgentEvent) -> str:
        """Convert an AgentEvent to JSON string"""
        return event.model_dump_json()
