from pydantic import BaseModel, Field
from typing import Any, Union, Literal, Dict, Optional, List, Self, Type
from datetime import datetime
from app.domain.models.plan import ExecutionStatus
from app.interfaces.schemas.file import FileInfoResponse
from app.domain.models.event import ToolStatus, ToolContent, BrowserToolContent
from app.domain.models.event import (
    AgentEvent,
    ErrorEvent,
    PlanEvent,
    MessageEvent,
    TitleEvent,
    ToolEvent,
    StepEvent,
    FileUpdateEvent,
)

class BaseEventData(BaseModel):
    event_id: Optional[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }

    @classmethod
    def base_event_data(cls, event: AgentEvent) -> dict:
        return {
            "event_id": event.id,
            "timestamp": int(event.timestamp.timestamp())
        }
    
    @classmethod
    def from_event(cls, event: AgentEvent) -> Self:
        return cls(
            **cls.base_event_data(event),
            **event.model_dump(exclude={"type", "id", "timestamp"})
        )

class CommonEventData(BaseEventData):
    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }
        extra = "allow"

class BaseStreamEvent(BaseModel):
    event: str
    data: BaseEventData

    @classmethod
    def from_event(cls, event: AgentEvent) -> Self:
        data_class: Type[BaseEventData] = cls.model_fields["data"].annotation or BaseEventData
        return cls(
            event=event.type,
            data=data_class.from_event(event)
        )

class MessageEventData(BaseEventData):
    role: Literal["user", "assistant"]
    content: str
    attachments: Optional[List[FileInfoResponse]] = None

class MessageStreamEvent(BaseStreamEvent):
    event: Literal["message"] = "message"
    data: MessageEventData

    @classmethod
    async def from_event_async(cls, event: MessageEvent) -> Self:
        return cls(
            data=MessageEventData(
                **BaseEventData.base_event_data(event),
                role=event.role,
                content=event.message,
                attachments=[await FileInfoResponse.from_domain(attachment) for attachment in event.attachments] if event.attachments else None
            )
        )

class ToolEventData(BaseEventData):
    tool_call_id: str
    name: str
    status: ToolStatus
    function: str
    args: Dict[str, Any]
    content: Optional[ToolContent] = None

class ToolStreamEvent(BaseStreamEvent):
    event: Literal["tool"] = "tool"
    data: ToolEventData

    @classmethod
    async def from_event_async(cls, event: ToolEvent) -> Self:
        content = event.tool_content
        if isinstance(content, BrowserToolContent):
            from app.interfaces.dependencies import get_file_service
            content = BrowserToolContent(screenshot=await get_file_service().create_signed_url(content.screenshot))
        return cls(
            data=ToolEventData(
                **BaseEventData.base_event_data(event),
                tool_call_id=event.tool_call_id,
                name=event.tool_name,
                status=event.status,
                function=event.function_name,
                args=event.function_args,
                content=content
            )
        )

class DoneStreamEvent(BaseStreamEvent):
    event: Literal["done"] = "done"

class WaitStreamEvent(BaseStreamEvent):
    event: Literal["wait"] = "wait"


class TerminalUpdateEventData(BaseEventData):
    shell_id: str
    output: Any = None
    description: Optional[str] = None


class TerminalUpdateStreamEvent(BaseStreamEvent):
    event: Literal["terminal_update"] = "terminal_update"
    data: TerminalUpdateEventData


class FileUpdateEventData(BaseEventData):
    path: str
    content: str = ""
    old_content: Optional[str] = None
    file: Optional[FileInfoResponse] = None


class FileUpdateStreamEvent(BaseStreamEvent):
    event: Literal["file_update"] = "file_update"
    data: FileUpdateEventData

    @classmethod
    async def from_event_async(cls, event: FileUpdateEvent) -> Self:
        file_resp = (
            await FileInfoResponse.from_domain(event.file) if event.file else None
        )
        return cls(
            data=FileUpdateEventData(
                **BaseEventData.base_event_data(event),
                path=event.path,
                content=event.content,
                old_content=event.old_content,
                file=file_resp,
            )
        )


class ErrorEventData(BaseEventData):
    error: str

class ErrorStreamEvent(BaseStreamEvent):
    event: Literal["error"] = "error"
    data: ErrorEventData

class StepEventData(BaseEventData):
    status: ExecutionStatus
    id: str
    description: str

class StepStreamEvent(BaseStreamEvent):
    event: Literal["step"] = "step"
    data: StepEventData

    @classmethod
    def from_event(cls, event: StepEvent) -> Self:
        return cls(
            data=StepEventData(
                **BaseEventData.base_event_data(event),
                status=event.step.status,
                id=event.step.id,
                description=event.step.description
            )
        )

class TitleEventData(BaseEventData):
    title: str

class TitleStreamEvent(BaseStreamEvent):
    event: Literal["title"] = "title"
    data: TitleEventData

class PlanEventData(BaseEventData):
    steps: List[StepEventData]

class PlanStreamEvent(BaseStreamEvent):
    event: Literal["plan"] = "plan"
    data: PlanEventData

    @classmethod
    def from_event(cls, event: PlanEvent) -> Self:
        return cls(
            data=PlanEventData(
                **BaseEventData.base_event_data(event),
                steps=[StepEventData(
                    **BaseEventData.base_event_data(event),
                    status=step.status,
                    id=step.id, 
                    description=step.description
                ) for step in event.plan.steps]
            )
        )

class CommonStreamEvent(BaseStreamEvent):
    event: str
    data: CommonEventData

AgentStreamEvent = Union[
    PlanStreamEvent,
    MessageStreamEvent,
    TitleStreamEvent,
    ToolStreamEvent,
    StepStreamEvent,
    DoneStreamEvent,
    ErrorStreamEvent,
    WaitStreamEvent,
    TerminalUpdateStreamEvent,
    FileUpdateStreamEvent,
    CommonStreamEvent,
]

# Explicit registry: domain event type -> wire stream event class.
# Register new event types here when adding them to AgentEvent.
_EVENT_TYPE_TO_STREAM_CLASS: Dict[str, Type[BaseStreamEvent]] = {
    "plan": PlanStreamEvent,
    "message": MessageStreamEvent,
    "title": TitleStreamEvent,
    "tool": ToolStreamEvent,
    "step": StepStreamEvent,
    "done": DoneStreamEvent,
    "error": ErrorStreamEvent,
    "wait": WaitStreamEvent,
    "terminal_update": TerminalUpdateStreamEvent,
    "file_update": FileUpdateStreamEvent,
}

class EventMapper:
    """Map AgentEvent (domain) to AgentStreamEvent (WS / REST wire format)"""

    @staticmethod
    async def event_to_stream_event(event: AgentEvent) -> AgentStreamEvent:
        stream_event_class = _EVENT_TYPE_TO_STREAM_CLASS.get(event.type, CommonStreamEvent)
        # Classes needing IO (e.g. signed URLs) define from_event_async
        from_event_async = getattr(stream_event_class, "from_event_async", None)
        if from_event_async is not None:
            return await from_event_async(event)
        return stream_event_class.from_event(event)

    @staticmethod
    async def events_to_stream_events(events: List[AgentEvent]) -> List[AgentStreamEvent]:
        """Create wire event list from domain event list"""
        return [
            await EventMapper.event_to_stream_event(event) for event in events if event
        ]
