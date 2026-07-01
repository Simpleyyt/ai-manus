from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Framework-neutral message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A tool call requested by the model, independent of any agent framework."""
    id: str = ""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """A framework-neutral conversation message.

    This is intentionally decoupled from any specific agent framework
    (LangChain, OpenAI Agents SDK, ...). Each engine adapter converts between
    this type and its framework's own message representation, so the domain and
    the persisted memory never depend on a particular framework.
    """
    role: Role
    content: Optional[str] = None
    # Populated on assistant messages that request tool calls.
    tool_calls: List[ToolCall] = Field(default_factory=list)
    # Populated on tool-result messages (role == TOOL).
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
