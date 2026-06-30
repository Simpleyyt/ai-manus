import logging
from pydantic import BaseModel, model_validator
from typing import List, Optional, Any
from app.domain.models.tool_result import ToolResult
from app.domain.models.llm_message import LLMMessage, Role

logger = logging.getLogger(__name__)

class Memory(BaseModel):
    """
    Memory class, defining the basic behavior of memory
    """
    messages: List[LLMMessage] = []

    @model_validator(mode="before")
    @classmethod
    def _drop_incompatible_messages(cls, data: Any) -> Any:
        """Tolerate legacy / unparseable persisted messages.

        Memory is persisted in MongoDB. Older deployments stored LangChain
        message objects, whose shape differs from LLMMessage. Rather than
        crashing when an old agent document is loaded, drop any message that
        cannot be coerced into LLMMessage (the affected session loses its LLM
        context, new sessions are unaffected).
        """
        if not isinstance(data, dict):
            return data
        raw_messages = data.get("messages")
        if not isinstance(raw_messages, list):
            return data
        kept: List[Any] = []
        for item in raw_messages:
            if isinstance(item, LLMMessage):
                kept.append(item)
                continue
            try:
                kept.append(LLMMessage.model_validate(item))
            except Exception:
                logger.warning("Dropping incompatible persisted memory message")
        data["messages"] = kept
        return data

    def add_message(self, message: LLMMessage) -> None:
        """Add message to memory"""
        self.messages.append(message)

    def add_messages(self, messages: List[LLMMessage]) -> None:
        """Add messages to memory"""
        self.messages.extend(messages)

    def get_messages(self) -> List[LLMMessage]:
        """Get all message history"""
        return self.messages

    def get_last_message(self) -> Optional[LLMMessage]:
        """Get the last message"""
        if len(self.messages) > 0:
            return self.messages[-1]
        return None

    def roll_back(self) -> None:
        """Roll back memory"""
        self.messages = self.messages[:-1]

    def compact(self) -> None:
        """Compact memory"""
        for message in self.messages:
            if message.role == Role.TOOL:
                if message.name in ["browser_view", "browser_navigate"]:
                    message.content = ToolResult(success=True, data='(removed)').model_dump_json()
                    logger.debug(f"Removed tool result from memory: {message.name}")

    @property
    def empty(self) -> bool:
        """Check if memory is empty"""
        return len(self.messages) == 0
