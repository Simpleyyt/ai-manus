import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


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

    Intentionally decoupled from any specific agent framework (LangChain,
    OpenAI Agents SDK, ...). Each engine adapter converts between this type and
    its framework's own message representation, so the domain and the persisted
    history never depend on a particular framework.
    """
    role: Role
    content: Optional[str] = None
    # Populated on assistant messages that request tool calls.
    tool_calls: List[ToolCall] = Field(default_factory=list)
    # Populated on tool-result messages (role == TOOL).
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class Conversation(BaseModel):
    """An agent's message history — the working, persisted conversation.

    This is the neutral unit passed to an :class:`AgentEngine`: the engine reads
    it as context and appends the messages it produces. It is framework-agnostic
    (holds :class:`ChatMessage`), so switching agent frameworks never changes
    what is stored.
    """
    messages: List[ChatMessage] = []

    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def add_messages(self, messages: List[ChatMessage]) -> None:
        self.messages.extend(messages)

    def get_messages(self) -> List[ChatMessage]:
        return self.messages

    def get_last_message(self) -> Optional[ChatMessage]:
        return self.messages[-1] if self.messages else None

    def roll_back(self) -> None:
        self.messages = self.messages[:-1]

    def compact(self) -> None:
        """Drop bulky tool results that are no longer needed as context."""
        for message in self.messages:
            if message.role == Role.TOOL and message.name in ["browser_view", "browser_navigate"]:
                message.content = ToolResult(success=True, data='(removed)').model_dump_json()
                logger.debug(f"Removed tool result from conversation: {message.name}")

    @property
    def empty(self) -> bool:
        return len(self.messages) == 0
