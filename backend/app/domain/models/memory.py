import json
import logging
from pydantic import BaseModel
from typing import List, Optional
from app.domain.models.message import LLMMessage, Role

logger = logging.getLogger(__name__)

# Rough chars-per-token ratio; conservative for mixed prose/code/JSON.
_CHARS_PER_TOKEN = 4

# Placeholder written over elided tool results. Kept as a ToolResult-shaped
# JSON string so downstream consumers can still parse the content.
_ELIDED_CONTENT = json.dumps(
    {"success": True, "message": "(result elided to save context)", "data": None}
)


def estimate_tokens(text: str) -> int:
    """Cheap, dependency-free token estimate for context budgeting."""
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


class Memory(BaseModel):
    """Agent conversation memory with token-aware compaction.

    Messages are stored append-only; :meth:`compact` reclaims context budget
    by eliding the *content* of old tool results (oldest first) while keeping
    the message skeleton intact, so tool-call pairing required by LLM APIs is
    never broken and recent working context is preserved.
    """
    messages: List[LLMMessage] = []

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

    def estimate_tokens(self) -> int:
        """Estimate the total token footprint of the stored messages."""
        total = 0
        for message in self.messages:
            total += estimate_tokens(message.content)
            for tool_call in message.tool_calls:
                total += estimate_tokens(tool_call.name)
                total += estimate_tokens(json.dumps(tool_call.args, default=str))
        return total

    def compact(self, max_tokens: int = 0, keep_recent: int = 10) -> None:
        """Elide old tool results until the memory fits the token budget.

        Args:
            max_tokens: Target context budget. ``0`` means "compact all
                eligible tool results" (unconditional cleanup between steps).
            keep_recent: Number of most recent messages that are never
                touched, so the model keeps its working context.
        """
        if max_tokens and self.estimate_tokens() <= max_tokens:
            return

        cutoff = max(0, len(self.messages) - keep_recent)
        for message in self.messages[:cutoff]:
            if message.role != Role.TOOL:
                continue
            if message.content == _ELIDED_CONTENT:
                continue
            message.content = _ELIDED_CONTENT
            logger.debug(f"Elided old tool result from memory: {message.name}")
            if max_tokens and self.estimate_tokens() <= max_tokens:
                return

    @property
    def empty(self) -> bool:
        """Check if memory is empty"""
        return len(self.messages) == 0
