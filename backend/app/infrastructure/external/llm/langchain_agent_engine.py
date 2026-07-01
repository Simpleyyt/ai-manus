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
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Tuple

from langchain.chat_models import init_chat_model
from langchain.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.tool import tool_call as create_tool_call

from app.domain.external.agent_engine import AgentEngine, LLMConfig, ResponseFormat
from app.domain.models.conversation import ChatMessage, Role, ToolCall
from app.domain.models.event import (
    AgentEvent,
    ErrorEvent,
    MessageEvent,
    ToolEvent,
    ToolStatus,
)
from app.domain.models.memory import Memory
from app.domain.models.tool_spec import ToolSpec
from app.infrastructure.external.llm.robust_json_parser import (
    RobustJsonParser,
    ToolCallParseError,
)

logger = logging.getLogger(__name__)


class LangChainAgentEngine(AgentEngine):
    """Runs a single agent turn (model call + tool-call loop) via LangChain."""

    def __init__(
        self,
        config: LLMConfig,
        *,
        max_iterations: int = 100,
        max_retries: int = 3,
        retry_interval: float = 1.0,
    ):
        self._max_iterations = max_iterations
        self._max_retries = max_retries
        self._retry_interval = retry_interval

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

    async def run(
        self,
        conversation: Memory,
        *,
        tools: Sequence[ToolSpec] = (),
        response_format: ResponseFormat = ResponseFormat.TEXT,
        allow_tools: bool = True,
    ) -> AsyncIterator[AgentEvent]:
        bound = self._bind(tools, response_format, allow_tools)
        tools_by_name = {spec.name: spec for spec in tools}

        message = await self._ask(bound, conversation)
        conversation.add_message(message)

        for _ in range(self._max_iterations):
            if not message.tool_calls:
                break

            tool_results: List[ChatMessage] = []
            for call in message.tool_calls:
                call.id = call.id or str(uuid.uuid4())
                spec = tools_by_name.get(call.name)
                if not spec:
                    yield ErrorEvent(error=f"Unknown tool: {call.name}")
                    continue

                yield self._tool_event(ToolStatus.CALLING, call, spec)
                result, content = await self._invoke(spec, call.arguments)
                yield self._tool_event(ToolStatus.CALLED, call, spec, result)

                tool_results.append(ChatMessage(
                    role=Role.TOOL,
                    tool_call_id=call.id,
                    name=call.name,
                    content=content,
                ))

            conversation.add_messages(tool_results)
            message = await self._ask(bound, conversation)
            conversation.add_message(message)
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")

        yield MessageEvent(message=message.content)

    # ------------------------------------------------------------------
    # Model call (with layered tool-call JSON repair, stages 4-5)
    # ------------------------------------------------------------------

    def _bind(self, tools: Sequence[ToolSpec], response_format: ResponseFormat, allow_tools: bool):
        model = self._model.bind(
            response_format={"type": response_format.value} if response_format is ResponseFormat.JSON else None,
            tool_choice=None if allow_tools else "none",
        )
        return model.bind_tools(self._build_tools(tools)) | RobustJsonParser.from_llm(self._model)

    async def _ask(self, chain, conversation: Memory) -> ChatMessage:
        context = [self._to_lc(message) for message in conversation.get_messages()]
        message: Optional[AIMessage] = None
        for attempt in range(self._max_retries):
            try:
                message = await chain.ainvoke(context)
                break
            except ToolCallParseError as e:
                if attempt == self._max_retries - 1:
                    raise
                logger.warning("Attempt %d/%d: tool call JSON repair failed, retrying model",
                               attempt + 1, self._max_retries)
                # Stage 4 (attempt 0): silent retry. Stage 5: add error feedback.
                if attempt > 0:
                    context = e.make_retry_context(context)
        return self._from_lc_ai(message)

    async def _invoke(self, spec: ToolSpec, args: Dict[str, Any]) -> Tuple[Any, str]:
        """Invoke a tool with retries.

        Returns ``(raw_result, content)`` on success, or ``(None, error)`` once
        all retries are exhausted.
        """
        for attempt in range(self._max_retries + 1):
            try:
                raw = await spec.handler(args)
                content = raw.model_dump_json() if hasattr(raw, "model_dump_json") else str(raw)
                return raw, content
            except Exception as e:
                if attempt >= self._max_retries:
                    logger.exception(f"Tool execution failed, {spec.name}, {args}")
                    return None, str(e)
                await asyncio.sleep(self._retry_interval)

    @staticmethod
    def _tool_event(status: ToolStatus, call: ToolCall, spec: ToolSpec, result: Any = None) -> ToolEvent:
        return ToolEvent(
            status=status,
            tool_call_id=call.id,
            tool_name=spec.toolkit_name,
            function_name=call.name,
            function_args=call.arguments,
            function_result=result,
        )

    # ------------------------------------------------------------------
    # Neutral <-> LangChain conversions
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tools(specs: Sequence[ToolSpec]) -> List[Dict[str, Any]]:
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
