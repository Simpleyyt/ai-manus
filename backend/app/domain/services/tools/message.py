from ast import And
from typing import List, Optional, Union
from app.domain.services.tools.base import BaseToolkit
from app.domain.models.tool_result import ToolResult
from langchain.tools import tool


class MessageToolkit(BaseToolkit):
    """Message tool class, providing message sending functions for user interaction"""

    name: str = "message"
    
    def __init__(self):
        """Initialize message tool class"""
        super().__init__()

    @tool(parse_docstring=True)
    async def message_notify_user(
        self,
        text: str
    ) -> ToolResult:
        """Send a message to user without requiring a response. Use for acknowledging receipt of messages, providing progress updates, reporting task completion, or explaining changes in approach.
        
        Args:
            text: Message text to display to user
        """
            
        # Return success result, actual UI display logic implemented by caller
        return ToolResult(success=True, data="Continue")
    
    @tool(parse_docstring=True)
    async def message_ask_user(
        self,
        text: str,
        attachments: Optional[Union[str, List[str]]] = None,
        suggest_user_takeover: Optional[str] = None
    ) -> ToolResult:
        """Ask user a question and wait for response. Use for requesting clarification, asking for confirmation, or gathering additional information.
        
        Args:
            text: Question text to present to user
            attachments: (Optional) List of question-related files or reference materials
            suggest_user_takeover: (Optional) Suggested operation for user takeover (enum: "none" or "browser")
        """
            
        # Return success result, actual UI interaction logic implemented by caller
        return ToolResult(success=True)
