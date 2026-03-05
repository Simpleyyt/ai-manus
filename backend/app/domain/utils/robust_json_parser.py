"""RobustJsonParser

A layered JSON repair pipeline for tool call arguments, implemented as a
LangChain Runnable[AIMessage, AIMessage] so it can be composed with a model
using the | operator:

    chain = model_with_tools | RobustJsonParser.from_llm(llm)

Repair stages applied in order when invalid_tool_calls are detected:

  Stage 1 — parse_partial_json   : repair truncated / incomplete JSON locally.
  Stage 2 — parse_json_markdown  : repair JSON wrapped in markdown code fences.
  Stage 3 — OutputFixingParser   : ask the LLM to rewrite only the broken JSON
                                   string (wraps JsonOutputParser, cheap call).

When stages 1-3 are all insufficient, a ToolCallParseError is raised.  The
caller can catch it and implement model-level retries (stages 4-5):

  Stage 4 — silent model retry   : re-invoke the chain without extra context
                                   (mirrors RetryOutputParser).
  Stage 5 — error model retry    : re-invoke with the failed AIMessage and
                                   error details appended (mirrors
                                   RetryWithErrorOutputParser).

Stages 4-5 are intentionally left to the caller so that the Runnable stays
composable and stateless.  ToolCallParseError exposes a make_retry_context()
helper to build the stage-5 context without duplicating the template.
"""
import asyncio
import logging
from typing import Any, Optional

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages.tool import tool_call as create_tool_call
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.utils.json import parse_json_markdown, parse_partial_json
from langchain_classic.output_parsers.fix import OutputFixingParser

logger = logging.getLogger(__name__)

_RETRY_WITH_ERROR_TEMPLATE = (
    "Your previous response contained invalid JSON in the tool call arguments.\n"
    "Error details:\n{error}\n\n"
    "Please resend the tool call with correctly formatted JSON arguments."
)


class ToolCallParseError(OutputParserException):
    """Raised when stages 1-3 cannot repair all invalid_tool_calls.

    Carries the partially-repaired AIMessage and per-call error details so
    callers can implement stages 4-5 (model-level retries) without
    re-discovering the errors.
    """

    def __init__(
        self,
        message: str,
        invalid_message: AIMessage,
        error_details: list[str],
    ) -> None:
        super().__init__(message)
        self.invalid_message = invalid_message
        self.error_details = error_details

    def make_retry_context(self, context: list[Any]) -> list[Any]:
        """Build a stage-5 context by appending error feedback to *context*.

        Args:
            context: Current conversation messages.

        Returns:
            A new list with the failed AIMessage and a corrective HumanMessage
            appended, ready to be passed back to the model.
        """
        error_str = "\n\n".join(self.error_details)
        return context + [
            self.invalid_message,
            HumanMessage(content=_RETRY_WITH_ERROR_TEMPLATE.format(error=error_str)),
        ]


class RobustJsonParser(Runnable[AIMessage, AIMessage]):
    """Layered JSON repair for tool call arguments (stages 1-3).

    Implements Runnable[AIMessage, AIMessage] so it composes cleanly with a
    bound model via the | operator::

        chain = (
            model
            .bind(response_format=..., tool_choice=...)
            .bind_tools(tools)
            | RobustJsonParser.from_llm(llm)
        )
        message = await chain.ainvoke(messages)

    Combines parse_partial_json, parse_json_markdown, JsonOutputParser, and
    OutputFixingParser into an escalating repair pipeline.  Raises
    ToolCallParseError (a subclass of OutputParserException) when all three
    stages are exhausted, so callers can add model-level retries (stages 4-5)
    on top — e.g. via chain.with_retry() or a manual loop.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm
        # Stage 3: OutputFixingParser wraps JsonOutputParser.
        # JsonOutputParser validates the fixed string is well-formed JSON;
        # OutputFixingParser drives one LLM repair call on failure.
        self._fixing_parser: OutputFixingParser = OutputFixingParser.from_llm(
            llm=llm,
            parser=JsonOutputParser(),
            max_retries=1,
        )

    @classmethod
    def from_llm(cls, llm: BaseChatModel) -> "RobustJsonParser":
        """Create a RobustJsonParser from a chat model.

        Args:
            llm: Chat model used for Stage 3 (OutputFixingParser) repair.

        Returns:
            A RobustJsonParser instance ready for use in a chain.
        """
        return cls(llm=llm)

    # ------------------------------------------------------------------
    # Stage 1: parse_partial_json
    # ------------------------------------------------------------------

    def _stage1_partial_json(self, raw: str) -> Optional[dict]:
        """Stage 1: tolerates truncated / incomplete JSON."""
        try:
            result = parse_partial_json(raw)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Stage 2: parse_json_markdown
    # ------------------------------------------------------------------

    def _stage2_json_markdown(self, raw: str) -> Optional[dict]:
        """Stage 2: strips markdown code fences before parsing."""
        try:
            result = parse_json_markdown(raw)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Stage 3: OutputFixingParser(JsonOutputParser)
    # ------------------------------------------------------------------

    async def _stage3_output_fixing(self, raw: str) -> Optional[dict]:
        """Stage 3: asks LLM to rewrite the broken JSON string."""
        try:
            result = await self._fixing_parser.aparse(raw)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Per-message repair (Stages 1-3)
    # ------------------------------------------------------------------

    async def _repair_invalid_tool_calls(self, message: AIMessage) -> AIMessage:
        """Attempt to repair each invalid_tool_call through stages 1-3.

        Repaired calls are promoted from invalid_tool_calls to tool_calls.
        Calls that cannot be repaired remain in invalid_tool_calls.
        """
        if not message.invalid_tool_calls:
            return message

        repaired_calls = list(message.tool_calls)
        still_invalid = []

        for itc in message.invalid_tool_calls:
            name: str = itc.get("name") or ""
            raw_args: str = itc.get("args") or ""

            fixed: Optional[dict] = (
                self._stage1_partial_json(raw_args)
                or self._stage2_json_markdown(raw_args)
                or await self._stage3_output_fixing(raw_args)
            )

            if fixed is not None:
                logger.info(
                    "Repaired invalid tool call '%s' (raw args length: %d)",
                    name,
                    len(raw_args),
                )
                repaired_calls.append(
                    create_tool_call(name=name, args=fixed, id=itc.get("id"))
                )
            else:
                still_invalid.append(itc)

        return message.model_copy(
            update={
                "tool_calls": repaired_calls,
                "invalid_tool_calls": still_invalid,
            }
        )

    def _collect_errors(self, message: AIMessage) -> list[str]:
        return [
            f"Tool '{itc.get('name', 'unknown')}': "
            f"{itc.get('error', 'JSON parse error')}\n"
            f"Raw arguments: {itc.get('args', '')}"
            for itc in (message.invalid_tool_calls or [])
        ]

    # ------------------------------------------------------------------
    # Runnable interface
    # ------------------------------------------------------------------

    def invoke(
        self,
        input: AIMessage,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AIMessage:
        return asyncio.get_event_loop().run_until_complete(
            self.ainvoke(input, config, **kwargs)
        )

    async def ainvoke(
        self,
        input: AIMessage,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AIMessage:
        """Repair invalid_tool_calls in *input* through stages 1-3.

        Args:
            input: The AIMessage produced by the model.
            config: Optional LangChain runnable config (unused but required by
                the Runnable interface).

        Returns:
            AIMessage with all tool call arguments successfully parsed.

        Raises:
            ToolCallParseError: If one or more tool calls cannot be repaired by
                stages 1-3.  The exception carries the partial-repaired
                AIMessage and per-call error details for the caller to use in
                stage-4/5 model retries.
        """
        message = await self._repair_invalid_tool_calls(input)

        if message.invalid_tool_calls:
            errors = self._collect_errors(message)
            raise ToolCallParseError(
                message=(
                    f"Tool call JSON repair failed ({len(message.invalid_tool_calls)} "
                    f"call(s) unrepairable).\n" + "\n".join(errors)
                ),
                invalid_message=message,
                error_details=errors,
            )

        return message
