from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Optional, Union, List, get_args
from datetime import datetime
import time
import uuid
from enum import Enum
from app.domain.models.plan import Plan, Step
from app.domain.models.file import FileInfo
import json


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

class McpToolContent(BaseModel):
    """MCP tool content"""
    result: Any

ToolContent = Union[BrowserToolContent, SearchToolContent, ShellToolContent, FileToolContent, McpToolContent]

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
    attachments: Optional[List[FileInfo]] = None

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
    WaitEvent,
]


class AgentEventFactory:
    """Factory class for JSON conversion and AgentEvent manipulation"""
    
    _EVENT_TYPES: Dict[str, type] = None
    
    @classmethod
    def _build_event_types(cls) -> Dict[str, type]:
        """Build event type mapping from AgentEvent Union types"""
        if cls._EVENT_TYPES is None:
            cls._EVENT_TYPES = {}
            # Get all types from AgentEvent Union
            union_types = get_args(AgentEvent)
            
            for event_type in union_types:
                # Skip BaseEvent as it's the fallback
                if event_type == BaseEvent:
                    continue
                
                # Get the literal type value from the class
                if hasattr(event_type, 'model_fields') and 'type' in event_type.model_fields:
                    field_info = event_type.model_fields['type']
                    if hasattr(field_info, 'default'):
                        type_value = field_info.default
                        cls._EVENT_TYPES[type_value] = event_type
        
        return cls._EVENT_TYPES
    
    @staticmethod
    def from_json(event_str: str) -> AgentEvent:
        """Create an AgentEvent from JSON string"""
        # Build event types mapping if not done yet
        event_types = AgentEventFactory._build_event_types()
        
        # Parse JSON to get the event type
        event_dict = json.loads(event_str)
        event_type = event_dict.get("type")
        
        # Get the appropriate class and parse
        event_class = event_types.get(event_type, BaseEvent)
        return event_class.model_validate_json(event_str)
    
    @staticmethod
    def to_json(event: AgentEvent) -> str:
        """Convert an AgentEvent to JSON string"""
        return event.model_dump_json()
