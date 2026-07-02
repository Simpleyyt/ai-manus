"""OpenAI SDK implementation of the domain :class:`LLM` gateway.

An alternative to :class:`app.infrastructure.external.llm.langchain_llm.LangchainLLM`
that talks to OpenAI (or any OpenAI-compatible endpoint) directly through the
official ``openai`` Python SDK, without going through LangChain.

Like the LangChain gateway it keeps all framework/SDK concerns — message
translation, tool binding, JSON repair and model-level retries — inside the
infrastructure layer, so the domain agents depend only on the
:class:`app.domain.external.llm.LLM` Protocol and domain message types.

Selected via ``LLM_BACKEND=openai``.
"""
import json
import logging
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.domain.models.message import LLMMessage, Role, ToolCall

logger = logging.getLogger(__name__)

_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)

_JSON_REPAIR_PROMPT = (
    "Extract or repair the JSON from the following LLM output. "
    "Respond with only the JSON object, nothing else.\n\n{text}"
)

_TOOL_ARGS_RETRY_PROMPT = (
    "Your previous response contained invalid JSON in the tool call arguments.\n"
    "Error details:\n{error}\n\n"
    "Please resend the tool call with correctly formatted JSON arguments."
)


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding ```json ... ``` markdown fence, if present."""
    without_open = _CODE_FENCE_RE.sub("", text, count=1)
    return _CODE_FENCE_RE.sub("", without_open, count=1).strip()


def _extract_json_object(text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Best-effort local extraction of a JSON object from raw model output.

    Tries the raw string, a markdown-fence-stripped variant, and finally the
    substring between the first ``{`` and last ``}``. Returns ``None`` when no
    JSON object can be recovered locally (callers then fall back to a model
    repair round-trip).
    """
    if not text:
        return None

    candidates = [text, text.strip(), _strip_code_fence(text)]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(obj, dict):
            return obj

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


class _ToolArgsParseError(Exception):
    """Raised internally when tool call arguments cannot be parsed as JSON."""

    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class OpenAILLM:
    """Concrete :class:`LLM` gateway backed by the OpenAI Python SDK."""

    def __init__(self, settings: Optional[Settings] = None, max_retries: int = 3):
        settings = settings or get_settings()
        self._model = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        self._max_retries = max_retries
        self._client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base,
            default_headers=settings.extra_headers or None,
        )

    # ------------------------------------------------------------------
    # Message translation (domain <-> OpenAI chat completion payloads)
    # ------------------------------------------------------------------

    def _to_openai(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for m in messages:
            if m.role == Role.SYSTEM:
                payload.append({"role": "system", "content": m.content})
            elif m.role == Role.USER:
                payload.append({"role": "user", "content": m.content})
            elif m.role == Role.ASSISTANT:
                msg: Dict[str, Any] = {
                    "role": "assistant",
                    # OpenAI accepts null content only when tool_calls are present.
                    "content": m.content or None,
                }
                if m.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.args or {}),
                            },
                        }
                        for tc in m.tool_calls
                    ]
                payload.append(msg)
            elif m.role == Role.TOOL:
                payload.append(
                    {
                        "role": "tool",
                        "tool_call_id": m.tool_call_id or "",
                        "content": m.content,
                    }
                )
        return payload

    def _from_openai(self, message: Any) -> LLMMessage:
        """Convert an OpenAI response message into a domain :class:`LLMMessage`.

        Raises:
            _ToolArgsParseError: if any tool call's ``arguments`` string cannot
                be parsed as a JSON object (caller retries the model).
        """
        tool_calls: List[ToolCall] = []
        errors: List[str] = []
        for tc in getattr(message, "tool_calls", None) or []:
            name = tc.function.name or ""
            raw_args = tc.function.arguments
            if raw_args is None or raw_args.strip() == "":
                args: Dict[str, Any] = {}
            else:
                parsed = _extract_json_object(raw_args)
                if parsed is None:
                    errors.append(f"Tool '{name}': invalid JSON arguments: {raw_args}")
                    continue
                args = parsed
            tool_calls.append(ToolCall(id=tc.id or "", name=name, args=args))

        if errors:
            raise _ToolArgsParseError(errors)

        return LLMMessage.assistant(content=message.content or "", tool_calls=tool_calls)

    # ------------------------------------------------------------------
    # LLM Protocol
    # ------------------------------------------------------------------

    async def _create(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[str],
        tool_choice: Optional[str],
    ) -> Any:
        kwargs: Dict[str, Any] = dict(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = {"type": response_format}
        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message

    async def ask(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[str] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMMessage:
        payload = self._to_openai(messages)
        for attempt in range(self._max_retries):
            raw = await self._create(payload, tools, response_format, tool_choice)
            try:
                message = self._from_openai(raw)
                logger.debug("Response from model: %s", message)
                return message
            except _ToolArgsParseError as e:
                if attempt == self._max_retries - 1:
                    raise
                logger.warning(
                    "Attempt %d/%d: tool call JSON parse failed, retrying model: %s",
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                if attempt > 0:
                    # Append the failed assistant turn plus corrective feedback.
                    payload = payload + [
                        raw.model_dump(exclude_none=True),
                        {
                            "role": "user",
                            "content": _TOOL_ARGS_RETRY_PROMPT.format(
                                error="\n".join(e.errors)
                            ),
                        },
                    ]
        # Unreachable: loop either returns or raises.
        raise _ToolArgsParseError(["exhausted retries"])

    async def parse_json(self, text: str) -> Dict[str, Any]:
        """Extract/repair a JSON object from raw model output."""
        local = _extract_json_object(text)
        if local is not None:
            return local

        logger.info("Local JSON extraction failed, asking model to repair")
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": _JSON_REPAIR_PROMPT.format(text=text)}
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        repaired = _extract_json_object(response.choices[0].message.content)
        if repaired is None:
            raise ValueError(f"Failed to parse JSON from model output: {text!r}")
        return repaired


@lru_cache()
def get_openai_llm() -> OpenAILLM:
    """Return a process-wide singleton OpenAI SDK LLM gateway."""
    logger.info("Creating OpenAILLM gateway")
    return OpenAILLM()
