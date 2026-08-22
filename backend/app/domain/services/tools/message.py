from typing import List, Optional, Union

from pydantic import BaseModel, Field

from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool


class MessageNotifyUserTool(Tool):
    name = "message_notify_user"
    description = (
        "Send a message to user without requiring a response. Use for acknowledging "
        "receipt of messages, providing progress updates, reporting task completion, "
        "or explaining changes in approach."
    )

    class Args(BaseModel):
        text: str = Field(description="Message text to display to user")

    async def run(self, text: str) -> ToolResult:
        return ToolResult(success=True, message="OK")


class MessageAskUserTool(Tool):
    name = "message_ask_user"
    description = (
        "Ask user a question and wait for response. Use for requesting "
        "clarification, asking for confirmation, or gathering additional information."
    )

    class Args(BaseModel):
        text: str = Field(description="Question text to present to user")
        attachments: Optional[Union[str, List[str]]] = Field(
            default=None,
            description="(Optional) List of question-related files or reference materials",
        )
        suggest_user_takeover: Optional[str] = Field(
            default=None,
            description='(Optional) Suggested operation for user takeover (enum: "none" or "browser")',
        )

    async def run(
        self,
        text: str,
        attachments: Optional[Union[str, List[str]]] = None,
        suggest_user_takeover: Optional[str] = None,
    ) -> ToolResult:
        return ToolResult(success=True)


class MessageToolkit(BaseToolkit):
    """Message tool class, providing message sending functions for user interaction"""

    name: str = "message"
    instructions: str = """
- Start tool-using work with message_notify_user (one short sentence ack)
- Use message_notify_user for brief one-sentence progress updates; it needs no reply
- Use message_ask_user only when blocked without user input (clarification, confirmation, credentials, or browser takeover)
- Prefer sensible defaults over asking when the request is already clear
- Do not dump raw todo lists as the user-facing answer
- When complete_step is available, end the current plan step with it (honest success/failure)
- When deliver_result is available, use it for the overall final answer and output files
"""
    tool_types = [MessageNotifyUserTool, MessageAskUserTool]

    def __init__(self):
        """Initialize message tool class"""
        super().__init__()
