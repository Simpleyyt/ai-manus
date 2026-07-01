import logging
import asyncio
import uuid
from abc import ABC
from typing import List, Optional, AsyncGenerator
from app.domain.models.message import Message, LLMMessage, Role, ToolCall
from app.domain.services.tools.base import BaseToolkit, Tool
from app.domain.models.event import (
    BaseEvent,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    MessageEvent,
)
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.external.llm import LLM


logger = logging.getLogger(__name__)
class BaseAgent(ABC):
    """
    Base agent class, defining the basic behavior of the agent
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
        llm: LLM,
        tools: List[BaseToolkit] = []
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self._llm = llm
        self.toolkits = tools
        self.memory = None

    async def _parse_json(self, text: str) -> dict:
        """Parse JSON from LLM output via the LLM gateway."""
        return await self._llm.parse_json(text)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get specified tool"""
        for toolkit in self.toolkits:
            tool = toolkit.get_tool(name)
            if tool:
                return tool
        return None

    def get_tool_schemas(self) -> List[dict]:
        """Get OpenAI function schemas for all available tools."""
        return [schema for toolkit in self.toolkits for schema in toolkit.get_tool_schemas()]

    async def invoke_tool(self, tool: Tool, tool_call: ToolCall) -> LLMMessage:
        """Invoke specified tool, with retry mechanism."""
        retries = 0
        last_error = ""
        while retries <= self.max_retries:
            try:
                raw_result = await tool.invoke(tool_call.args)
                content = (
                    raw_result.model_dump_json()
                    if hasattr(raw_result, "model_dump_json")
                    else str(raw_result)
                )
                return LLMMessage.tool(
                    tool_call_id=tool_call.id,
                    name=tool.name,
                    content=content,
                    artifact=raw_result,
                )
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(self.retry_interval)
                else:
                    logger.exception(f"Tool execution failed, {tool_call.name}, {tool_call.args}")
                    break

        return LLMMessage.tool(tool_call_id=tool_call.id, name=tool.name, content=last_error)
    
    async def execute(self, request: str, format: Optional[str] = None) -> AsyncGenerator[BaseEvent, None]:
        format = format or self.format
        message = await self.ask(request, format)
        for _ in range(self.max_iterations):
            if not message.tool_calls:
                break
            tool_responses = []
            for tool_call in message.tool_calls:
                function_name = tool_call.name
                if not tool_call.id:
                    tool_call.id = str(uuid.uuid4())
                tool_call_id = tool_call.id
                function_args = tool_call.args
                
                tool = self.get_tool(function_name)
                if not tool:
                    yield ErrorEvent(error=f"Unknown tool: {function_name}")
                    continue

                # Generate event before tool call
                yield ToolEvent(
                    status=ToolStatus.CALLING,
                    tool_call_id=tool_call_id,
                    tool_name=tool.toolkit.name,
                    function_name=function_name,
                    function_args=function_args
                )

                tool_result = await self.invoke_tool(tool, tool_call)

                # Generate event after tool call
                yield ToolEvent(
                    status=ToolStatus.CALLED,
                    tool_call_id=tool_call_id,
                    tool_name=tool.toolkit.name,
                    function_name=function_name,
                    function_args=function_args,
                    function_result=tool_result.artifact
                )

                tool_responses.append(tool_result)

            message = await self.ask_with_messages(tool_responses)
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")
        
        yield MessageEvent(message=message.content)
    
    async def _ensure_memory(self):
        if not self.memory:
            self.memory = await self._repository.get_memory(self._agent_id, self.name)
    
    async def _add_to_memory(self, messages: List[LLMMessage]) -> None:
        """Update memory and save to repository"""
        await self._ensure_memory()
        if self.memory.empty:
            self.memory.add_message(LLMMessage.system(self.system_prompt))
        self.memory.add_messages(messages)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
    
    async def _roll_back_memory(self) -> None:
        await self._ensure_memory()
        self.memory.roll_back()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def ask_with_messages(self, messages: List[LLMMessage], format: Optional[str] = None) -> LLMMessage:
        await self._add_to_memory(messages)

        context = list(self.memory.get_messages())
        message = await self._llm.ask(
            messages=context,
            tools=self.get_tool_schemas(),
            response_format=format,
            tool_choice=self.tool_choice,
        )
        logger.debug(f"Response from model: {message}")

        await self._add_to_memory([message])
        return message

    async def ask(self, request: str, format: Optional[str] = None) -> LLMMessage:
        return await self.ask_with_messages([
            LLMMessage.user(request)
        ], format)
    
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
        function_name = tool_call.name
        tool_call_id = tool_call.id
        if function_name == "message_ask_user":
            self.memory.add_message(LLMMessage.tool(tool_call_id=tool_call_id, name=function_name, content=message.message))
        else:
            self.memory.roll_back()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
    
    async def compact_memory(self) -> None:
        await self._ensure_memory()
        self.memory.compact()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
