"""LangChain-backed implementation of the domain LLM gateway.

All LangChain coupling for the agent loop lives here: model construction, tool
binding, message conversion, JSON repair and retry. The domain layer only sees
the framework-agnostic ``LLMMessage`` type and the ``LLM`` protocol.
"""
import logging
from typing import Any, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_classic.output_parsers.retry import RetryWithErrorOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.core.config import get_settings
from app.domain.external.llm import LLM
from app.domain.models.llm_message import LLMMessage, ToolCall, Role
from app.infrastructure.external.llm.robust_json_parser import (
    RobustJsonParser,
    ToolCallParseError,
)

logger = logging.getLogger(__name__)

_JSON_PARSE_PROMPT = PromptTemplate.from_template(
    "Extract or repair the JSON from the following LLM output.\n\n{input}"
)


class LangChainLLM(LLM):
    """Concrete LLM gateway built on LangChain's ``init_chat_model``."""

    max_retries: int = 3

    def __init__(self) -> None:
        settings = get_settings()
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        kwargs = dict(
            model=settings.model_name,
            model_provider=settings.model_provider,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            base_url=settings.api_base,
        )
        if settings.extra_headers:
            kwargs["default_headers"] = settings.extra_headers
        self._model = init_chat_model(**kwargs)
        self._json_output_parser = RetryWithErrorOutputParser.from_llm(
            parser=JsonOutputParser(),
            llm=self._model,
            max_retries=self.max_retries,
        )

    # ------------------------------------------------------------------
    # Message conversion (domain <-> langchain)
    # ------------------------------------------------------------------

    def _to_langchain(self, message: LLMMessage) -> AnyMessage:
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
        # assistant
        tool_calls = [
            {"name": tc.name, "args": tc.args, "id": tc.id, "type": "tool_call"}
            for tc in message.tool_calls
        ]
        return AIMessage(content=message.content or "", tool_calls=tool_calls)

    def _from_langchain(self, message: AIMessage) -> LLMMessage:
        content = message.content if isinstance(message.content, str) else str(message.content or "")
        tool_calls = [
            ToolCall(id=tc.get("id") or "", name=tc.get("name") or "", args=tc.get("args") or {})
            for tc in (message.tool_calls or [])
        ]
        return LLMMessage.assistant(content=content, tool_calls=tool_calls)

    # ------------------------------------------------------------------
    # LLM protocol
    # ------------------------------------------------------------------

    async def ask(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[str] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMMessage:
        bound = self._model.bind(
            response_format={"type": response_format} if response_format else None,
            tool_choice=tool_choice,
        )
        if tools:
            bound = bound.bind_tools(tools)
        chain = bound | RobustJsonParser.from_llm(self._model)

        context: List[AnyMessage] = [self._to_langchain(m) for m in messages]
        message: Optional[AIMessage] = None
        for attempt in range(self.max_retries):
            try:
                message = await chain.ainvoke(context)
                break
            except ToolCallParseError as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    "Attempt %d/%d: tool call JSON repair failed, retrying model",
                    attempt + 1, self.max_retries,
                )
                if attempt == 0:
                    # Stage 4 (RetryOutputParser style): silent retry, same context.
                    pass
                else:
                    # Stage 5 (RetryWithErrorOutputParser style): add error feedback.
                    context = e.make_retry_context(context)

        return self._from_langchain(message)

    async def parse_json(self, text: str) -> dict:
        prompt_value = _JSON_PARSE_PROMPT.format_prompt(input=text)
        return await self._json_output_parser.aparse_with_prompt(text, prompt_value)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens
