from typing import List, Optional, Union
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class MessageTool(BaseTool):
    """Message tool class, providing message sending functions for user interaction"""

    name: str = "message"
    
    def __init__(self):
        """Initialize message tool class"""
        super().__init__()
        
    @tool(
        name="message_notify_user",
        description="Send a message to user without requiring a response. Use for acknowledging receipt of messages, providing progress updates, reporting task completion, or explaining changes in approach.",
        parameters={
            "text": {
                "type": "string",
                "description": "Message text to display to user"
            }
        },
        required=["text"]
    )
    async def message_notify_user(
        self,
        text: str
    ) -> ToolResult:
        """Send notification message to user, no response needed
        
        Args:
            text: Message text to display to user
            
        Returns:
            Message sending result
        """
            
        # Return success result, actual UI display logic implemented by caller
        return ToolResult(success=True)
    
    @tool(
        name="message_ask_user",
        description="Ask user a question and wait for response. Use for requesting clarification, asking for confirmation, or gathering additional information.",
        parameters={
            "text": {
                "type": "string",
                "description": "Question text to present to user"
            },
            "attachments": {
                "anyOf": [
                    {"type": "string"},
                    {"items": {"type": "string"}, "type": "array"}
                ],
                "description": "(Optional) List of question-related files or reference materials"
            },
            "suggest_user_takeover": {
                "type": "string",
                "enum": ["none", "browser"],
                "description": "(Optional) Suggested operation for user takeover"
            }
        },
        required=["text"]
    )
    async def message_ask_user(
        self,
        text: str,
        attachments: Optional[Union[str, List[str]]] = None,
        suggest_user_takeover: Optional[str] = None
    ) -> ToolResult:
        """Ask user a question and wait for response
        
        Args:
            text: Question text to present to user
            attachments: List of question-related files or reference materials
            suggest_user_takeover: Suggested operation for user takeover
            
        Returns:
            Question asking result with user response
        """
            
        # Return success result, actual UI interaction logic implemented by caller
        return ToolResult(success=True)