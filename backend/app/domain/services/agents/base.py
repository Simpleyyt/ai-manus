import json
import logging
import asyncio
import re
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.domain.external.llm import LLM
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.models.message import Message
from app.domain.services.tools.base import BaseTool
from app.domain.models.tool_result import ToolResult
from app.domain.models.event import (
    BaseEvent,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    MessageEvent,
    DoneEvent,
    DeltaEvent,
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
    max_iterations: int = 100
    max_retries: int = 3
    retry_interval: float = 1.0
    tool_choice: Optional[str] = None

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

        return ToolResult(success=False, message=last_error)

    async def execute(self, request: str, format: Optional[str] = None) -> AsyncGenerator[BaseEvent, None]:
        format = format or self.format
        final_message = None
        async for message in self.ask(request=request, format=format):
            if 'delta' in message:
                yield DeltaEvent(
                    content=message["delta"],
                )
            else:
                final_message = message

        for _ in range(self.max_iterations):
            if not final_message.get("tool_calls"):
                break
            tool_responses = []
            for tool_call in final_message["tool_calls"]:
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
                    "function_name": function_name,
                    "tool_call_id": tool_call_id,
                    "content": result.model_dump_json()
                }
                tool_responses.append(tool_response)

            async for message in self.ask_with_messages(tool_responses):
                if 'delta' in message:
                    yield DeltaEvent(
                        content=message["delta"],
                    )
                else:
                    final_message = message
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")

        yield MessageEvent(message=final_message["content"])

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

    async def _roll_back_memory(self) -> None:
        await self._ensure_memory()
        self.memory.roll_back()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def ask_with_messages(self, messages: List[Dict[str, Any]], format: Optional[str] = None) -> AsyncGenerator[
        Dict[str, Any], None]:
        await self._add_to_memory(messages)

        response_format = None
        if format:
            response_format = {"type": format}

        for _ in range(self.max_retries):
            # message = await self.llm.ask_stream(self.memory.get_messages(),
            #                                 tools=self.get_available_tools(),
            #                                 response_format=response_format,
            #                                 tool_choice=self.tool_choice)
            content = ""
            streamed_message=""
            current_tool_call = None
            try:
                async for delta in self.llm.ask_stream(
                        self.memory.get_messages(),
                        tools=self.get_available_tools(),
                        response_format=response_format,
                        tool_choice=self.tool_choice
                ):
                    if not delta or delta.get("role") != "assistant":
                        logger.warning(f"Unknown delta role: {delta.get('role')}")
                        await self._add_to_memory([delta])
                        continue

                    delta_content = delta.get("content") or ""
                    if not delta_content and not delta.get("tool_calls"):
                        # 既没有文本增量也没有工具调用，直接跳过即可
                        continue

                    content += delta_content

                    if delta.get("tool_calls"):
                        if isinstance(delta.get("tool_calls"), dict):
                            current_tool_call = self._merge_function_calls(current_tool_call,
                                                                           delta.get("tool_calls"))
                        elif isinstance(delta.get("tool_calls"), list):
                            for tool_call in delta.get("tool_calls"):
                                current_tool_call = self._merge_function_calls(current_tool_call, tool_call)

                    full_message = self._extract_message_from_partial_json(content)
                    if not full_message:
                        # 说明 message 这一字段里目前还看不出新增的完整字符，先不推给前端
                        continue
                    new_part = full_message[len(streamed_message):]
                    if not new_part:
                        # full_message 和之前的一样，没有新增内容
                        continue
                    streamed_message = full_message
                    yield {
                        "role": "assistant",
                        "delta": new_part,
                    }
            except Exception as e:
                logger.error(f"Error in streaming chat: {e}")

            if not content.strip() and not current_tool_call:
                logger.warning(f"Assistant message has no content, retry")
                await self._add_to_memory([
                    {"role": "assistant", "content": ""},
                    {"role": "user", "content": "no thinking, please continue"}
                ])
                continue
            filtered_message = {"role": "assistant", "content": content,
                                "tool_calls": [current_tool_call] if current_tool_call else []}
            await self._add_to_memory([filtered_message])
            yield filtered_message
            break
        else:
            raise Exception(f"Empty response from LLM after {self.max_retries} retries")

    async def ask(self, request: str, format: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        async for message in self.ask_with_messages([
            {
                "role": "user", "content": request
            }
        ], format):
            yield message

    async def roll_back(self, message: Message):
        await self._ensure_memory()
        last_message = self.memory.get_last_message()
        if (not last_message or
                not last_message.get("tool_calls") or
                len(last_message.get("tool_calls")) == 0):
            return
        tool_call = last_message.get("tool_calls")[0]
        function_name = tool_call.get("function", {}).get("name")
        tool_call_id = tool_call.get("id")
        if function_name == "message_ask_user":
            self.memory.add_message({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "function_name": function_name,
                "content": message.model_dump_json()
            })
        else:
            self.memory.roll_back()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def compact_memory(self) -> None:
        await self._ensure_memory()
        self.memory.compact()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    @staticmethod
    def _merge_function_calls(a: dict, b: dict) -> dict:
        if a is None:
            a = {}
        a.setdefault("type", "function")
        a.setdefault("id", b.get("id"))

        b_func = b.get("function")
        if not b_func:
            return a

        a_func = a.setdefault("function", {})
        for key in ("arguments", "name"):
            if key in b_func and b_func[key]:
                a_func[key] = (a_func.get(key) or "") + b_func[key]

        return a

    @staticmethod
    def _extract_message_from_partial_json(buffer: str) -> str:
        """
        从不完整的 JSON 字符串中，尽可能提取出 `message` 或 `result` 字段当前的完整值。
        """
        m = re.search(r'"(message|result)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)', buffer)
        if not m:
            return ""

        field_name = m.group(1)
        raw = m.group(2)

        try:
            return json.loads(f'"{raw}"')
        except Exception:
            return ""