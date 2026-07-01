import logging
from pydantic import BaseModel
from typing import List, Optional
from app.domain.models.tool_result import ToolResult
from app.domain.models.conversation import ChatMessage, Role

logger = logging.getLogger(__name__)

class Memory(BaseModel):
    """
    Memory class, defining the basic behavior of memory.

    Holds framework-neutral :class:`ChatMessage` objects so that neither the
    domain nor the persisted conversation depends on a specific agent framework.
    """
    messages: List[ChatMessage] = []

    def add_message(self, message: ChatMessage) -> None:
        """Add message to memory"""
        self.messages.append(message)
    
    def add_messages(self, messages: List[ChatMessage]) -> None:
        """Add messages to memory"""
        self.messages.extend(messages)

    def get_messages(self) -> List[ChatMessage]:
        """Get all message history"""
        return self.messages
    
    def get_last_message(self) -> Optional[ChatMessage]:
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
