"""Persistence adapter (anti-corruption layer) for agent memory.

All knowledge about *how memory is stored on disk* — including the two
historical wire formats — lives here in the infrastructure layer, so the
domain :class:`LLMMessage` model stays framework-agnostic and only understands
its own native shape.

Supported inbound (persisted) message shapes:

* Native domain shape: ``{"role", "content", "tool_calls":[{"id","name","args"}],
  "tool_call_id", "name"}``.
* LangChain ``model_dump`` shape: discriminated by a ``type`` field
  (``system`` / ``human`` / ``ai`` / ``tool``) with extra keys such as
  ``additional_kwargs``, ``invalid_tool_calls`` and ``status``.
* Old OpenAI chat shape: ``role`` based, tool messages use ``function_name``,
  tool calls nested under ``function`` with a stringified ``arguments``.
"""
import json
from typing import Any, Dict, List, Optional

from app.domain.models.memory import Memory
from app.domain.models.message import LLMMessage

# LangChain message ``type`` discriminator -> domain role.
_LANGCHAIN_TYPE_TO_ROLE = {
    "system": "system",
    "human": "user",
    "ai": "assistant",
    "tool": "tool",
}


def _coerce_args(args: Any) -> Dict[str, Any]:
    """Normalise persisted tool-call arguments into a dict."""
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        if not args.strip():
            return {}
        try:
            parsed = json.loads(args)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def _upgrade_tool_call(raw: Any) -> Dict[str, Any]:
    """Upgrade a persisted tool call into the native ``{id, name, args}`` shape."""
    if not isinstance(raw, dict):
        return {"id": "", "name": "", "args": {}}
    # OpenAI wire format: {"id", "type", "function": {"name", "arguments"}}
    if isinstance(raw.get("function"), dict):
        fn = raw["function"]
        return {
            "id": raw.get("id") or "",
            "name": fn.get("name", ""),
            "args": _coerce_args(fn.get("arguments")),
        }
    # Native / LangChain shape: {"id", "name", "args"} (+ maybe "type").
    return {
        "id": raw.get("id") or "",
        "name": raw.get("name", ""),
        "args": _coerce_args(raw.get("args")),
    }


def _upgrade_message(raw: Any) -> Dict[str, Any]:
    """Upgrade a single persisted message dict into a native LLMMessage dict."""
    if not isinstance(raw, dict):
        return raw
    data = dict(raw)

    # LangChain shape: map the "type" discriminator to a role.
    if "role" not in data and "type" in data:
        lc_type = data.pop("type")
        data["role"] = _LANGCHAIN_TYPE_TO_ROLE.get(lc_type, lc_type)

    # Old OpenAI persisted tool messages carried "function_name".
    if data.get("role") == "tool" and not data.get("name") and data.get("function_name"):
        data["name"] = data.get("function_name")

    if data.get("content") is None:
        data["content"] = ""

    if data.get("tool_calls"):
        data["tool_calls"] = [_upgrade_tool_call(tc) for tc in data["tool_calls"]]

    # Keep only fields the domain model recognises; drop framework extras
    # (additional_kwargs, response_metadata, invalid_tool_calls, status, ...).
    allowed = {"role", "content", "tool_calls", "tool_call_id", "name"}
    return {k: v for k, v in data.items() if k in allowed}


def deserialize_memory(raw: Optional[Dict[str, Any]]) -> Memory:
    """Build a domain :class:`Memory` from its persisted representation."""
    if not raw:
        return Memory()
    raw_messages: List[Any] = raw.get("messages", []) or []
    messages = [LLMMessage.model_validate(_upgrade_message(m)) for m in raw_messages]
    return Memory(messages=messages)


def serialize_memory(memory: Memory) -> Dict[str, Any]:
    """Render a domain :class:`Memory` into its persisted representation."""
    return memory.model_dump()
