from pydantic import BaseModel, Field
from typing import Any, Union, Literal, Dict, Optional, List
import time
from app.domain.models.plan import ExecutionStatus
from app.domain.events.agent_events import ToolStatus
from app.domain.events.agent_events import (
    AgentEvent,
    DoneEvent,
    ErrorEvent,
    PlanEvent,
    MessageEvent,
    TitleEvent,
    ToolEvent,
    StepEvent,
    WaitEvent,
)


class BaseEventData(BaseModel):
    event_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time()))

class MessageEventData(BaseEventData):
    role: Literal["user", "assistant"]
    content: str

class ToolEventData(BaseEventData):
    tool_call_id: str
    name: str
    status: ToolStatus
    function: str
    args: Dict[str, Any]
    content: Optional[Any] = None

class StepEventData(BaseEventData):
    status: ExecutionStatus
    id: str
    description: str


class PlanEventData(BaseEventData):
    steps: List[StepEventData]

class ErrorEventData(BaseEventData):
    error: str

class TitleEventData(BaseEventData):
    title: str

class BaseSSEEvent(BaseModel):
    event: str
    data: Optional[Union[str, BaseEventData]]

class MessageSSEEvent(BaseSSEEvent):
    event: Literal["message"] = "message"
    data: MessageEventData

class ToolSSEEvent(BaseSSEEvent):
    event: Literal["tool"] = "tool"
    data: ToolEventData

class DoneSSEEvent(BaseSSEEvent):
    event: Literal["done"] = "done"
    data: BaseEventData

class WaitSSEEvent(BaseSSEEvent):
    event: Literal["wait"] = "wait"
    data: BaseEventData

class ErrorSSEEvent(BaseSSEEvent):
    event: Literal["error"] = "error"
    data: ErrorEventData

class StepSSEEvent(BaseSSEEvent):
    event: Literal["step"] = "step"
    data: StepEventData

class TitleSSEEvent(BaseSSEEvent):
    event: Literal["title"] = "title"
    data: TitleEventData

class PlanSSEEvent(BaseSSEEvent):
    event: Literal["plan"] = "plan"
    data: PlanEventData

AgentSSEEvent = Union[
    BaseSSEEvent,
    PlanSSEEvent,
    MessageSSEEvent,
    TitleSSEEvent,
    ToolSSEEvent,
    StepSSEEvent,
    DoneSSEEvent,
    ErrorSSEEvent,
    WaitSSEEvent
]

class SSEEventFactory:
    @staticmethod
    def from_events(events: List[AgentEvent]) -> List[AgentSSEEvent]:
        return list(filter(lambda x: x is not None, [
            SSEEventFactory.from_event(event) for event in events if event
        ]))
    
    @staticmethod
    def from_event(event: AgentEvent) -> Optional[AgentSSEEvent]:
        base_event = BaseEventData(
            event_id=event.id,
            timestamp=int(event.timestamp.timestamp())
        )
        
        if isinstance(event, PlanEvent):
            return PlanSSEEvent(
                data=PlanEventData(
                    **base_event.model_dump(),
                    steps=[StepEventData(
                        status=step.status,
                        id=step.id, 
                        description=step.description
                    ) for step in event.plan.steps]
                )
            )
        elif isinstance(event, MessageEvent):
            return MessageSSEEvent(
                data=MessageEventData(
                    **base_event.model_dump(),
                    content=event.message,
                    role=event.role
                )
            )
        elif isinstance(event, TitleEvent):
            return TitleSSEEvent(
                data=TitleEventData(
                    **base_event.model_dump(),
                    title=event.title
                )
            )
        elif isinstance(event, ToolEvent):
            return ToolSSEEvent(
                data=ToolEventData(
                    **base_event.model_dump(),
                    tool_call_id=event.tool_call_id,
                    name=event.tool_name,
                    function=event.function_name,
                    args=event.function_args,
                    status=event.status,
                    content=event.tool_content
                )
            )
        elif isinstance(event, StepEvent):
            return StepSSEEvent(
                data=StepEventData(
                    **base_event.model_dump(),
                    status=event.step.status,
                    id=event.step.id, 
                    description=event.step.description
                )
            )
        elif isinstance(event, DoneEvent):
            return DoneSSEEvent(data=base_event)
        elif isinstance(event, ErrorEvent):
            return ErrorSSEEvent(
                data=ErrorEventData(
                    **base_event.model_dump(),
                    error=event.error
                )
            )
        elif isinstance(event, WaitEvent):
            return WaitSSEEvent(data=base_event)