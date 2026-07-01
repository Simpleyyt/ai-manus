import logging
from abc import ABC
from typing import List, Optional, AsyncGenerator
from app.domain.models.message import Message
from app.domain.models.conversation import ChatMessage, Role
from app.domain.models.event import BaseEvent
from app.domain.models.tool_spec import ToolSpec
from app.domain.services.tools.base import BaseToolkit
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.external.agent_engine import AgentEngine, ResponseFormat
from app.domain.utils.json_parse import parse_json_lenient


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base agent class, defining the basic behavior of the agent.

    The agent owns its prompt, its persisted conversation (memory) and how the
    memory is rolled back / compacted, but delegates the actual model call and
    tool-call loop to an injected :class:`AgentEngine`. This keeps the agent
    (and the plan-act flow above it) independent of any concrete agent
    framework.
    """

    name: str = ""
    system_prompt: str = ""
    format: ResponseFormat = ResponseFormat.TEXT
    allow_tools: bool = True

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        engine: AgentEngine,
        tools: List[BaseToolkit] = [],
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self._engine = engine
        self.toolkits = tools
        self._tool_specs: List[ToolSpec] = [
            spec for toolkit in tools for spec in toolkit.to_tool_specs()
        ]
        self.conversation = None

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from an assistant's final structured output."""
        return parse_json_lenient(text)

    async def execute(self, request: str) -> AsyncGenerator[BaseEvent, None]:
        """Run one agent turn: assemble the conversation, stream engine events,
        and persist the conversation as it changes."""
        await self._ensure_conversation()
        if self.conversation.empty:
            self.conversation.add_message(ChatMessage(role=Role.SYSTEM, content=self.system_prompt))
        self.conversation.add_message(ChatMessage(role=Role.USER, content=request))
        await self._save_conversation()
        try:
            async for event in self._engine.run(
                self.conversation,
                tools=self._tool_specs,
                response_format=self.format,
                allow_tools=self.allow_tools,
            ):
                yield event
                await self._save_conversation()
        finally:
            await self._save_conversation()

    async def _ensure_conversation(self):
        if not self.conversation:
            self.conversation = await self._repository.get_conversation(self._agent_id, self.name)

    async def _save_conversation(self) -> None:
        await self._repository.save_conversation(self._agent_id, self.name, self.conversation)

    async def roll_back(self, message: Message):
        await self._ensure_conversation()
        last_message = self.conversation.get_last_message()
        if not last_message:
            return
        if last_message.role != Role.ASSISTANT:
            return
        if not last_message.tool_calls:
            return
        tool_call = last_message.tool_calls[0]
        if tool_call.name == "message_ask_user":
            self.conversation.add_message(ChatMessage(
                role=Role.TOOL,
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=message.message,
            ))
        else:
            self.conversation.roll_back()
        await self._save_conversation()

    async def compact_conversation(self) -> None:
        await self._ensure_conversation()
        self.conversation.compact()
        await self._save_conversation()
