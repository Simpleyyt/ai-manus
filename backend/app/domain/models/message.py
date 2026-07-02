from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """User-facing input message (a chat turn from the user)."""
    message: str = ""
    attachments: List[str] = []


class Role(str, Enum):
    """Conversation roles, framework-agnostic."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A single tool/function call requested by the assistant."""
    id: str = ""
    name: str = ""
    args: Dict[str, Any] = {}


class LLMMessage(BaseModel):
    """Domain-native conversation message.

    A framework-agnostic representation of a single message in an agent
    conversation. Translation to/from any specific LLM framework, and adapting
    historical persisted formats, is the responsibility of the infrastructure
    layer (the LLM gateway and the memory persistence adapter) — this model
    only knows its own native shape.
    """

    role: Role
    content: str = ""
    tool_calls: List[ToolCall] = []
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    # Raw tool result object, kept only in memory for event rendering; never
    # persisted (excluded from model_dump).
    artifact: Optional[Any] = Field(default=None, exclude=True)

    @field_validator("content", mode="before")
    @classmethod
    def _content_never_none(cls, value: Any) -> str:
        return "" if value is None else value

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: str = "",
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> "LLMMessage":
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls or [])

    @classmethod
    def tool(
        cls,
        tool_call_id: str,
        name: str,
        content: str,
        artifact: Any = None,
    ) -> "LLMMessage":
        return cls(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            artifact=artifact,
        )
