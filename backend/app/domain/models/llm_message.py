from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A single tool/function call requested by the model."""
    id: str = ""
    name: str = ""
    args: Dict[str, Any] = {}


class LLMMessage(BaseModel):
    """Domain-native conversation message.

    Framework-agnostic replacement for LangChain message objects. This is the
    structure persisted in agent memory (``AgentDocument.memories``), so any
    change here affects the on-disk schema.
    """
    role: Role
    content: Optional[str] = None
    # Only meaningful for assistant messages
    tool_calls: List[ToolCall] = Field(default_factory=list)
    # Only meaningful for tool messages
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> "LLMMessage":
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls or [],
        )

    @classmethod
    def tool(cls, tool_call_id: str, name: str, content: str) -> "LLMMessage":
        return cls(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
        )
