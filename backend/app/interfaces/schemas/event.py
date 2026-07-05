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

class BaseSSEEvent(BaseModel):
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

class MessageSSEEvent(BaseSSEEvent):
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

class ToolSSEEvent(BaseSSEEvent):
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

class DoneSSEEvent(BaseSSEEvent):
    event: Literal["done"] = "done"

class WaitSSEEvent(BaseSSEEvent):
    event: Literal["wait"] = "wait"

class ErrorEventData(BaseEventData):
    error: str

class ErrorSSEEvent(BaseSSEEvent):
    event: Literal["error"] = "error"
    data: ErrorEventData

class StepEventData(BaseEventData):
    status: ExecutionStatus
    id: str
    description: str

class StepSSEEvent(BaseSSEEvent):
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

class TitleSSEEvent(BaseSSEEvent):
    event: Literal["title"] = "title"
    data: TitleEventData

class PlanEventData(BaseEventData):
    steps: List[StepEventData]

class PlanSSEEvent(BaseSSEEvent):
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

class CommonSSEEvent(BaseSSEEvent):
    event: str
    data: CommonEventData

AgentSSEEvent = Union[
    PlanSSEEvent,
    MessageSSEEvent,
    TitleSSEEvent,
    ToolSSEEvent,
    StepSSEEvent,
    DoneSSEEvent,
    ErrorSSEEvent,
    WaitSSEEvent,
    CommonSSEEvent,
]

# Explicit registry: domain event type -> SSE event class.
# Register new event types here when adding them to AgentEvent.
_EVENT_TYPE_TO_SSE_CLASS: Dict[str, Type[BaseSSEEvent]] = {
    "plan": PlanSSEEvent,
    "message": MessageSSEEvent,
    "title": TitleSSEEvent,
    "tool": ToolSSEEvent,
    "step": StepSSEEvent,
    "done": DoneSSEEvent,
    "error": ErrorSSEEvent,
    "wait": WaitSSEEvent,
}

class EventMapper:
    """Map AgentEvent (domain) to SSEEvent (wire format)"""

    @staticmethod
    async def event_to_sse_event(event: AgentEvent) -> AgentSSEEvent:
        sse_event_class = _EVENT_TYPE_TO_SSE_CLASS.get(event.type, CommonSSEEvent)
        # Classes needing IO (e.g. signed URLs) define from_event_async
        from_event_async = getattr(sse_event_class, "from_event_async", None)
        if from_event_async is not None:
            return await from_event_async(event)
        return sse_event_class.from_event(event)

    @staticmethod
    async def events_to_sse_events(events: List[AgentEvent]) -> List[AgentSSEEvent]:
        """Create SSE event list from event list"""
        return [
            await EventMapper.event_to_sse_event(event) for event in events if event
        ]