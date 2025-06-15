import json
import logging
import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.domain.external.llm import LLM
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.services.tools.base import BaseTool
from app.domain.models.tool_result import ToolResult
from app.domain.events.agent_events import (
    BaseEvent,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    MessageEvent,
    DoneEvent,
)
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.utils.json_parser import JsonParser

logger = logging.getLogger(__name__)
class BaseAgent(ABC):
    """
    Base agent class, defining the basic behavior of the agent
    """

    name: str = ""
    system_prompt: str = ""
    format: Optional[str] = None
    max_iterations: int = 30
    max_retries: int = 3
    retry_interval: float = 1.0

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        json_parser: JsonParser,
        tools: List[BaseTool] = []
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self.llm = llm
        self.json_parser = json_parser
        self.tools = tools
        self.memory = None
    
    def get_available_tools(self) -> Optional[List[Dict[str, Any]]]:
        """Get all available tools list"""
        available_tools = []
        for tool in self.tools:
            available_tools.extend(tool.get_tools())
        return available_tools
    
    def get_tool(self, function_name: str) -> BaseTool:
        """Get specified tool"""
        for tool in self.tools:
            if tool.has_function(function_name):
                return tool
        raise ValueError(f"Unknown tool: {function_name}")

    async def invoke_tool(self, tool: BaseTool, function_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Invoke specified tool, with retry mechanism"""

        retries = 0
        while retries <= self.max_retries:
            try:
                return await tool.invoke_function(function_name, **arguments)
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(self.retry_interval)
                else:
                    logger.exception(f"Tool execution failed, {function_name}, {arguments}")
                    break
        
        #raise ValueError(f"Tool execution failed, retried {self.max_retries} times: {last_error}")
        return ToolResult(success=False, error=last_error)
    
    async def execute(self, request: str) -> AsyncGenerator[BaseEvent, None]:
        message = await self.ask(request, self.format)
        for _ in range(self.max_iterations):
            if not message.get("tool_calls"):
                break
            tool_responses = []
            for tool_call in message["tool_calls"]:
                if not tool_call.get("function"):
                    continue
                
                function_name = tool_call["function"]["name"]
                tool_call_id = tool_call["id"] or str(uuid.uuid4())
                function_args = await self.json_parser.parse(tool_call["function"]["arguments"])
                
                tool = self.get_tool(function_name)

                # Generate event before tool call
                yield ToolEvent(
                    status=ToolStatus.CALLING,
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args
                )

                result = await self.invoke_tool(tool, function_name, function_args)
                
                # Generate event after tool call
                yield ToolEvent(
                    status=ToolStatus.CALLED,
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    function_result=result
                )

                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result.model_dump_json()
                }
                tool_responses.append(tool_response)

            message = await self.ask_with_messages(tool_responses)
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")
        
        yield MessageEvent(message=message["content"])
    
    async def _ensure_memory(self):
        if not self.memory:
            self.memory = await self._repository.get_memory(self._agent_id, self.name)
    
    async def _add_to_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Update memory and save to repository"""
        await self._ensure_memory()
        if self.memory.empty:
            self.memory.add_message({
                "role": "system", "content": self.system_prompt,
            })
        self.memory.add_messages(messages)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def ask_with_messages(self, messages: List[Dict[str, Any]], format: Optional[str] = None) -> Dict[str, Any]:
        await self._add_to_memory(messages)

        response_format = None
        if format:
            response_format = {"type": format}

        message = await self.llm.ask(self.memory.get_messages(), 
                                     tools=self.get_available_tools(), 
                                     response_format=response_format)
        if message.get("tool_calls"):
            message["tool_calls"] = message["tool_calls"][:1]
        await self._add_to_memory([message])
        return message

    async def ask(self, request: str, format: Optional[str] = None) -> Dict[str, Any]:
        return await self.ask_with_messages([
            {
                "role": "user", "content": request
            }
        ], format)
    
    async def roll_back(self):
        await self._ensure_memory()
        last_message = self.memory.get_last_message()
        if not last_message:
            return
        if not last_message.get("tool_calls"):
            return
        tool_responses = []
        for tool_call in last_message.get("tool_calls"):
            tool_call_id = tool_call["id"] or str(uuid.uuid4())
            tool_responses.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": ToolResult(success=True).model_dump_json()
            })
        await self._add_to_memory(tool_responses)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
