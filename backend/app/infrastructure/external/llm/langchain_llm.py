"""LangChain implementation of the domain :class:`LLM` gateway.

Keeps all LangChain-specific concerns — model instantiation, message
translation, tool binding, the JSON-repair chain and model-level retries —
inside the infrastructure layer, so the domain agents depend only on the
:class:`app.domain.external.llm.LLM` Protocol and domain message types.
"""
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_classic.output_parsers.retry import RetryWithErrorOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.config import Settings, get_settings
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.infrastructure.external.llm.robust_json_parser import (
    RobustJsonParser,
    ToolCallParseError,
)

logger = logging.getLogger(__name__)


class LangchainLLM:
    """Concrete :class:`LLM` gateway backed by LangChain chat models."""

    _JSON_PARSE_PROMPT = PromptTemplate.from_template(
        "Extract or repair the JSON from the following LLM output.\n\n{input}"
    )

    def __init__(self, settings: Optional[Settings] = None, max_retries: int = 3):
        settings = settings or get_settings()
        self._max_retries = max_retries

        kwargs: Dict[str, Any] = dict(
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
            max_retries=self._max_retries,
        )

    # ------------------------------------------------------------------
    # Message translation (domain <-> LangChain)
    # ------------------------------------------------------------------

    def _to_langchain(self, messages: List[LLMMessage]) -> List[Any]:
        lc_messages: List[Any] = []
        for m in messages:
            if m.role == Role.SYSTEM:
                lc_messages.append(SystemMessage(content=m.content))
            elif m.role == Role.USER:
                lc_messages.append(HumanMessage(content=m.content))
            elif m.role == Role.ASSISTANT:
                tool_calls = [
                    {
                        "name": tc.name,
                        "args": tc.args,
                        "id": tc.id or None,
                        "type": "tool_call",
                    }
                    for tc in m.tool_calls
                ]
                lc_messages.append(
                    AIMessage(content=m.content, tool_calls=tool_calls)
                )
            elif m.role == Role.TOOL:
                lc_messages.append(
                    ToolMessage(
                        tool_call_id=m.tool_call_id or "",
                        name=m.name,
                        content=m.content,
                    )
                )
        return lc_messages

    def _from_langchain(self, message: AIMessage) -> LLMMessage:
        tool_calls = [
            ToolCall(
                id=tc.get("id") or "",
                name=tc.get("name") or "",
                args=tc.get("args") or {},
            )
            for tc in (message.tool_calls or [])
        ]
        raw = message.content
        if isinstance(raw, str):
            content = raw
        elif raw is None:
            content = ""
        else:
            content = str(raw)
        return LLMMessage.assistant(content=content, tool_calls=tool_calls)

    # ------------------------------------------------------------------
    # LLM Protocol
    # ------------------------------------------------------------------

    async def ask(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[str] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMMessage:
        rf = {"type": response_format} if response_format else None

        model = self._model.bind(response_format=rf, tool_choice=tool_choice)
        if tools:
            model = model.bind_tools(tools)

        # Stages 1-3: RobustJsonParser repairs invalid tool call JSON locally
        # and via a cheap fixing call. Stages 4-5: this outer loop retries the
        # model, silently first then with error feedback.
        chain = model | RobustJsonParser.from_llm(self._model)

        context = self._to_langchain(messages)
        message: Optional[AIMessage] = None
        for attempt in range(self._max_retries):
            try:
                message = await chain.ainvoke(context)
                break
            except ToolCallParseError as e:
                if attempt == self._max_retries - 1:
                    raise
                logger.warning(
                    "Attempt %d/%d: tool call JSON repair failed, retrying model",
                    attempt + 1,
                    self._max_retries,
                )
                if attempt > 0:
                    # Stage 5: append the failed message and error feedback.
                    context = e.make_retry_context(context)

        logger.debug("Response from model: %s", message)
        return self._from_langchain(message)

    async def parse_json(self, text: str) -> Dict[str, Any]:
        """Extract/repair a JSON object from raw model output."""
        prompt_value = self._JSON_PARSE_PROMPT.format_prompt(input=text)
        return await self._json_output_parser.aparse_with_prompt(text, prompt_value)


@lru_cache()
def get_llm() -> LangchainLLM:
    """Return a process-wide singleton LangChain LLM gateway."""
    logger.info("Creating LangchainLLM gateway")
    return LangchainLLM()
