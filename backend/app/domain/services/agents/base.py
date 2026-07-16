import logging
import asyncio
import uuid
from abc import ABC
from typing import Any, List, Literal, Optional, AsyncGenerator
from app.domain.models.message import Message, LLMMessage, Role, ToolCall
from app.domain.services.tools.base import BaseToolkit, OutputTool, Tool, ValidationError
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


class StructuredOutputEvent(BaseEvent):
    """Internal event carrying validated structured output.

    Emitted when the model submits its result through an :class:`OutputTool`.
    Consumed by the concrete agents; never part of the public
    ``AgentEvent`` union streamed to clients.
    """

    type: Literal["structured_output"] = "structured_output"
    output: Any


class BaseAgent(ABC):
    """
    Base agent class, defining the basic behavior of the agent
    """

    name: str = ""
    max_iterations: int = 100
    max_retries: int = 3
    retry_interval: float = 1.0
    tool_choice: Optional[str] = None
    # Context engineering budgets: tool results are truncated at ingestion,
    # and memory is compacted before each model call when over budget.
    max_tool_result_chars: int = 16000
    max_context_tokens: int = 100000

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
        self._output_tool: Optional[OutputTool] = None

    def build_system_prompt(self) -> str:
        """Assemble the system prompt for this agent; overridden by subclasses."""
        return ""

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get specified tool"""
        for toolkit in self.toolkits:
            tool = toolkit.get_tool(name)
            if tool:
                return tool
        return None

    def get_tool_schemas(self) -> List[dict]:
        """Get OpenAI function schemas for all available tools.

        Includes the active output tool, if any, so the model can submit
        structured results through native function calling.
        """
        schemas = [schema for toolkit in self.toolkits for schema in toolkit.get_tool_schemas()]
        if self._output_tool:
            schemas.append(self._output_tool.to_openai_schema())
        return schemas

    def _truncate_tool_result(self, content: str) -> str:
        """Cap a tool result before it enters memory, to bound context growth."""
        if len(content) <= self.max_tool_result_chars:
            return content
        omitted = len(content) - self.max_tool_result_chars
        return (
            content[: self.max_tool_result_chars]
            + f"... [truncated {omitted} chars to save context]"
        )

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
                    content=self._truncate_tool_result(content),
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

    def _handle_output_call(self, tool_call: ToolCall) -> tuple[LLMMessage, Optional[Any]]:
        """Validate a structured-output tool call.

        Returns the tool response message to append to memory and, on
        success, the validated output model. On validation failure the
        response carries the error so the model can self-repair on the next
        iteration.
        """
        try:
            output = self._output_tool.validate(tool_call.args)
            response = LLMMessage.tool(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content='{"success": true}',
            )
            return response, output
        except ValidationError as e:
            logger.warning(f"Structured output validation failed for {tool_call.name}: {e}")
            response = LLMMessage.tool(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Invalid arguments, please correct and call {tool_call.name} again: {e}",
            )
            return response, None

    async def execute(
        self,
        request: str,
        output_tool: Optional[OutputTool] = None,
    ) -> AsyncGenerator[BaseEvent, None]:
        """Run the agent loop.

        The model works with native tool calling. When ``output_tool`` is
        provided, the loop finishes when the model calls it with valid
        arguments, yielding a :class:`StructuredOutputEvent`. Otherwise a
        plain assistant message ends the loop with a :class:`MessageEvent`.
        """
        self._output_tool = output_tool
        try:
            message = await self.ask(request)
            for _ in range(self.max_iterations):
                if not message.tool_calls:
                    # Plain message: final answer for unstructured runs; for
                    # structured runs, nudge the model to use the output tool.
                    if not output_tool:
                        break
                    message = await self.ask(
                        f"Submit your result by calling the `{output_tool.name}` tool."
                    )
                    continue

                tool_responses = []
                structured_output: Optional[Any] = None
                for tool_call in message.tool_calls:
                    function_name = tool_call.name
                    if not tool_call.id:
                        tool_call.id = str(uuid.uuid4())
                    tool_call_id = tool_call.id
                    function_args = tool_call.args

                    if output_tool and function_name == output_tool.name:
                        response, structured_output = self._handle_output_call(tool_call)
                        tool_responses.append(response)
                        continue

                    tool = self.get_tool(function_name)
                    if not tool:
                        yield ErrorEvent(error=f"Unknown tool: {function_name}")
                        tool_responses.append(LLMMessage.tool(
                            tool_call_id=tool_call_id,
                            name=function_name,
                            content=f"Unknown tool: {function_name}",
                        ))
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

                if structured_output is not None:
                    # Persist the tool responses so the tool-call pairing in
                    # memory stays consistent, then finish.
                    await self._add_to_memory(tool_responses)
                    yield StructuredOutputEvent(output=structured_output)
                    return

                message = await self.ask_with_messages(tool_responses)
            else:
                yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")

            yield MessageEvent(message=message.content)
        finally:
            self._output_tool = None

    async def _ensure_memory(self):
        if not self.memory:
            self.memory = await self._repository.get_memory(self._agent_id, self.name)
    
    async def _add_to_memory(self, messages: List[LLMMessage]) -> None:
        """Update memory and save to repository"""
        await self._ensure_memory()
        if self.memory.empty:
            self.memory.add_message(LLMMessage.system(self.build_system_prompt()))
        self.memory.add_messages(messages)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
    
    async def _roll_back_memory(self) -> None:
        await self._ensure_memory()
        self.memory.roll_back()
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def ask_with_messages(self, messages: List[LLMMessage]) -> LLMMessage:
        await self._add_to_memory(messages)

        # Token-aware guard: reclaim budget from old tool results before the
        # context is sent to the model.
        if self.memory.estimate_tokens() > self.max_context_tokens:
            self.memory.compact(max_tokens=self.max_context_tokens)
            await self._repository.save_memory(self._agent_id, self.name, self.memory)

        context = list(self.memory.get_messages())
        message = await self._llm.ask(
            messages=context,
            tools=self.get_tool_schemas(),
            tool_choice=self.tool_choice,
        )
        logger.debug(f"Response from model: {message}")

        await self._add_to_memory([message])
        return message

    async def ask(self, request: str) -> LLMMessage:
        return await self.ask_with_messages([
            LLMMessage.user(request)
        ])
    
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
