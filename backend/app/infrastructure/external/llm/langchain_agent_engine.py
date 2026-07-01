"""LangChain implementation of the AgentEngine port.

All LangChain coupling for the agent runtime lives here: model construction,
tool binding, the model + tool-call loop, and tool-call JSON repair. The domain
(BaseAgent / PlanActFlow) only depends on the framework-neutral
:class:`AgentEngine` Protocol, so swapping to another agent framework means
adding another adapter alongside this one.
"""
import asyncio
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from langchain.chat_models import init_chat_model
from langchain.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.tool import tool_call as create_tool_call

from app.domain.external.agent_engine import AgentEngine, AgentRunRequest, LLMConfig
from app.domain.models.conversation import ChatMessage, Role, ToolCall
from app.domain.models.event import (
    BaseEvent,
    ErrorEvent,
    MessageEvent,
    ToolEvent,
    ToolStatus,
)
from app.domain.models.tool_spec import ToolSpec
from app.infrastructure.external.llm.robust_json_parser import (
    RobustJsonParser,
    ToolCallParseError,
)

logger = logging.getLogger(__name__)


class LangChainAgentEngine(AgentEngine):
    """Runs a single agent turn (model call + tool-call loop) via LangChain."""

    def __init__(self, config: LLMConfig):
        self._config = config
        kwargs: Dict[str, Any] = dict(
            model=config.model_name,
            model_provider=config.model_provider,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url=config.api_base,
        )
        if config.extra_headers:
            kwargs["default_headers"] = config.extra_headers
        self._model = init_chat_model(**kwargs)

    async def run(self, request: AgentRunRequest) -> AsyncGenerator[BaseEvent, None]:
        memory = request.memory
        if memory.empty:
            memory.add_message(ChatMessage(role=Role.SYSTEM, content=request.system_prompt))
        memory.add_message(ChatMessage(role=Role.USER, content=request.user_input))
        await self._progress(request)

        lc_tools = self._build_tools(request.tools)
        tools_by_name = {spec.name: spec for spec in request.tools}
        response_format = {"type": request.response_format} if request.response_format else None

        ai_message = await self._ask(memory, lc_tools, response_format, request.tool_choice, request.max_retries)
        memory.add_message(ai_message)
        await self._progress(request)

        for _ in range(request.max_iterations):
            if not ai_message.tool_calls:
                break

            tool_messages: List[ChatMessage] = []
            for tool_call in ai_message.tool_calls:
                tool_call.id = tool_call.id or str(uuid.uuid4())
                spec = tools_by_name.get(tool_call.name)
                if not spec:
                    yield ErrorEvent(error=f"Unknown tool: {tool_call.name}")
                    continue

                yield ToolEvent(
                    status=ToolStatus.CALLING,
                    tool_call_id=tool_call.id,
                    tool_name=spec.toolkit_name,
                    function_name=tool_call.name,
                    function_args=tool_call.arguments,
                )

                result, content = await self._invoke(spec, tool_call.arguments, request)

                yield ToolEvent(
                    status=ToolStatus.CALLED,
                    tool_call_id=tool_call.id,
                    tool_name=spec.toolkit_name,
                    function_name=tool_call.name,
                    function_args=tool_call.arguments,
                    function_result=result,
                )

                tool_messages.append(ChatMessage(
                    role=Role.TOOL,
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=content,
                ))

            memory.add_messages(tool_messages)
            await self._progress(request)

            ai_message = await self._ask(memory, lc_tools, response_format, request.tool_choice, request.max_retries)
            memory.add_message(ai_message)
            await self._progress(request)
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")

        yield MessageEvent(message=ai_message.content)

    # ------------------------------------------------------------------
    # Model call (with layered tool-call JSON repair, stages 4-5)
    # ------------------------------------------------------------------

    async def _ask(
        self,
        memory,
        lc_tools: List[Dict[str, Any]],
        response_format: Optional[Dict[str, str]],
        tool_choice: Optional[str],
        max_retries: int,
    ) -> ChatMessage:
        chain = (
            self._model
            .bind(response_format=response_format, tool_choice=tool_choice)
            .bind_tools(lc_tools)
            | RobustJsonParser.from_llm(self._model)
        )

        context = [self._to_lc(message) for message in memory.get_messages()]
        message: Optional[AIMessage] = None
        for attempt in range(max_retries):
            try:
                message = await chain.ainvoke(context)
                break
            except ToolCallParseError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Attempt %d/%d: tool call JSON repair failed, retrying model",
                    attempt + 1, max_retries,
                )
                if attempt == 0:
                    # Stage 4: silent retry, same context.
                    pass
                else:
                    # Stage 5: add error feedback to context.
                    context = e.make_retry_context(context)
        logger.debug(f"Response from model: {message}")
        return self._from_lc_ai(message)

    async def _invoke(
        self,
        spec: ToolSpec,
        args: Dict[str, Any],
        request: AgentRunRequest,
    ) -> Tuple[Any, str]:
        """Invoke a tool with retries.

        Returns ``(raw_result, content)`` on success, or ``(None, error)`` when
        all retries are exhausted.
        """
        retries = 0
        last_error = ""
        while retries <= request.max_retries:
            try:
                raw = await spec.handler(args)
                content = raw.model_dump_json() if hasattr(raw, "model_dump_json") else str(raw)
                return raw, content
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= request.max_retries:
                    await asyncio.sleep(request.retry_interval)
                else:
                    logger.exception(f"Tool execution failed, {spec.name}, {args}")
        return None, last_error

    async def _progress(self, request: AgentRunRequest) -> None:
        if request.on_progress:
            await request.on_progress()

    # ------------------------------------------------------------------
    # Neutral <-> LangChain conversions
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tools(specs: List[ToolSpec]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
            for spec in specs
        ]

    @staticmethod
    def _to_lc(message: ChatMessage):
        if message.role == Role.SYSTEM:
            return SystemMessage(content=message.content or "")
        if message.role == Role.USER:
            return HumanMessage(content=message.content or "")
        if message.role == Role.TOOL:
            return ToolMessage(
                content=message.content or "",
                tool_call_id=message.tool_call_id or "",
                name=message.name or "",
            )
        # Assistant
        tool_calls = [
            create_tool_call(name=tc.name, args=tc.arguments, id=tc.id or None)
            for tc in message.tool_calls
        ]
        return AIMessage(content=message.content or "", tool_calls=tool_calls)

    @staticmethod
    def _from_lc_ai(message: AIMessage) -> ChatMessage:
        tool_calls = [
            ToolCall(id=tc.get("id") or "", name=tc["name"], arguments=tc.get("args") or {})
            for tc in (message.tool_calls or [])
        ]
        content = message.content if isinstance(message.content, str) else str(message.content)
        return ChatMessage(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)
