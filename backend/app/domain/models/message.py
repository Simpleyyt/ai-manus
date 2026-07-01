import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Message(BaseModel):
    """User-facing input message (a chat turn from the user)."""
    message: str = ""
    attachments: List[str] = []


class Role(str, Enum):
    """Conversation roles, framework-agnostic (mirrors OpenAI chat roles)."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# LangChain message ``type`` discriminator -> domain role. Kept at module level
# (not a class attribute) so pydantic does not treat it as a private attribute.
_LANGCHAIN_TYPE_TO_ROLE = {
    "system": "system",
    "human": "user",
    "ai": "assistant",
    "tool": "tool",
}


def _coerce_args(args: Any) -> Dict[str, Any]:
    """Normalise tool call arguments into a dict.

    Accepts already-parsed dicts as well as JSON strings (the shape used by
    the OpenAI wire format and some historical persisted records).
    """
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


class ToolCall(BaseModel):
    """A single tool/function call requested by the assistant."""
    id: str = ""
    name: str = ""
    args: Dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # OpenAI wire format: {"id", "type", "function": {"name", "arguments"}}
        if "function" in data and isinstance(data["function"], dict):
            fn = data["function"]
            data["name"] = fn.get("name", data.get("name", ""))
            data["args"] = _coerce_args(fn.get("arguments"))
            data.pop("function", None)
        elif "args" in data:
            data["args"] = _coerce_args(data.get("args"))
        # LangChain tool calls may carry a "type" discriminator; drop it.
        data.pop("type", None)
        if data.get("id") is None:
            data["id"] = ""
        return data


class LLMMessage(BaseModel):
    """Domain-native conversation message.

    Replaces LangChain message objects inside the domain so business logic and
    persistence no longer depend on a specific LLM framework. Includes a
    permissive ``before`` validator that upgrades two historical persisted
    shapes into this model:

    * LangChain ``model_dump`` shape (discriminated by a ``type`` field:
      ``system`` / ``human`` / ``ai`` / ``tool``).
    * OpenAI chat shape (``role`` based, tool messages use ``function_name``,
      tool calls nested under ``function`` with stringified ``arguments``).
    """

    model_config = ConfigDict(extra="ignore")

    role: Role
    content: str = ""
    tool_calls: List[ToolCall] = []
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    # Raw tool result object, kept only in memory for event rendering; never
    # persisted (excluded from model_dump).
    artifact: Optional[Any] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)

        # LangChain shape: map "type" discriminator to a role.
        if "role" not in data and "type" in data:
            lc_type = data.pop("type")
            data["role"] = _LANGCHAIN_TYPE_TO_ROLE.get(lc_type, lc_type)

        # Old OpenAI persisted tool messages used "function_name".
        if data.get("role") == "tool" and not data.get("name") and data.get("function_name"):
            data["name"] = data.get("function_name")

        return data

    @field_validator("content", mode="before")
    @classmethod
    def _content_never_none(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        # LangChain permits list-of-parts content; flatten to text.
        if isinstance(value, list):
            parts = [p if isinstance(p, str) else str(p) for p in value]
            return "".join(parts)
        return str(value)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: str = "",
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> "LLMMessage":
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls or [])

    @classmethod
    def tool(
        cls,
        tool_call_id: str,
        name: str,
        content: str,
        artifact: Any = None,
    ) -> "LLMMessage":
        return cls(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            artifact=artifact,
        )
