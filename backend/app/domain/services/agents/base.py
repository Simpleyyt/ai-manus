import logging
from abc import ABC
from typing import List, Optional, AsyncGenerator
from app.domain.models.message import Message
from app.domain.models.conversation import ChatMessage, Role
from app.domain.models.event import BaseEvent
from app.domain.models.tool_spec import ToolSpec
from app.domain.services.tools.base import BaseToolkit
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.external.agent_engine import AgentEngine, AgentRunRequest
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
    format: Optional[str] = None
    max_iterations: int = 100
    max_retries: int = 3
    retry_interval: float = 1.0
    tool_choice: Optional[str] = None

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
        self.memory = None

    async def _parse_json(self, text: str) -> dict:
        """Parse JSON from an assistant's final structured output."""
        return parse_json_lenient(text)

    async def execute(self, request: str, format: Optional[str] = None) -> AsyncGenerator[BaseEvent, None]:
        """Run one agent turn via the engine, persisting memory as it changes."""
        await self._ensure_memory()
        run_request = AgentRunRequest(
            system_prompt=self.system_prompt,
            memory=self.memory,
            user_input=request,
            tools=self._tool_specs,
            response_format=format or self.format,
            tool_choice=self.tool_choice,
            max_iterations=self.max_iterations,
            max_retries=self.max_retries,
            retry_interval=self.retry_interval,
            on_progress=self._save_memory,
        )
        try:
            async for event in self._engine.run(run_request):
                yield event
        finally:
            await self._save_memory()

    async def _ensure_memory(self):
        if not self.memory:
            self.memory = await self._repository.get_memory(self._agent_id, self.name)

    async def _save_memory(self) -> None:
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def roll_back(self, message: Message):
        await self._ensure_memory()
        last_message = self.memory.get_last_message()
        if not last_message:
            return
        if last_message.role != Role.ASSISTANT:
            return
        if not last_message.tool_calls:
            return
        tool_call = last_message.tool_calls[0]
        if tool_call.name == "message_ask_user":
            self.memory.add_message(ChatMessage(
                role=Role.TOOL,
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=message.message,
            ))
        else:
            self.memory.roll_back()
        await self._save_memory()

    async def compact_memory(self) -> None:
        await self._ensure_memory()
        self.memory.compact()
        await self._save_memory()
