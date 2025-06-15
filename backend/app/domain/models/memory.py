from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Memory(BaseModel):
    """
    Memory class, defining the basic behavior of memory
    """
    messages: List[Dict[str, Any]] = []

    def get_message_role(self, message: Dict[str, Any]) -> str:
        """Get the role of the message"""
        return message.get("role")

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add message to memory"""
        self.messages.append(message)
    
    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Add messages to memory"""
        self.messages.extend(messages)

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all message history"""
        return self.messages

    def get_latest_system_message(self) -> Dict[str, Any]:
        """Get the latest system message"""
        for message in reversed(self.messages):
            if self.get_message_role(message) == "system":
                return message
        return {}

    def get_non_system_messages(self) -> List[Dict[str, Any]]:
        """Get all non-system messages"""
        return [message for message in self.messages if self.get_message_role(message) != "system"]

    def get_messages_with_latest_system(self) -> List[Dict[str, Any]]:
        """Get all non-system messages plus the latest system message"""
        latest_system = self.get_latest_system_message()
        non_system_messages = self.get_non_system_messages()
        if latest_system:
            return [latest_system] + non_system_messages
        return non_system_messages
    
    def clear_messages(self) -> None:
        """Clear memory"""
        self.messages = []
    
    def get_filtered_messages(self) -> List[Dict[str, Any]]:
        """Get all non-system and non-tool response messages, plus the latest system message"""
        latest_system = self.get_latest_system_message()
        messages = [message for message in self.messages 
                  if self.get_message_role(message) != "system"]
                  #and self.get_message_role(message) != "tool"]
        if latest_system:
            return [latest_system] + messages
        return messages
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get the last message"""
        if len(self.messages) > 0:  
            return self.messages[-1]
        return None

    @property
    def empty(self) -> bool:
        """Check if memory is empty"""
        return len(self.messages) == 0
