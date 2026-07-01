from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Dict, Optional, Protocol, Sequence, runtime_checkable

from app.domain.models.event import AgentEvent
from app.domain.models.memory import Memory
from app.domain.models.tool_spec import ToolSpec


class ResponseFormat(str, Enum):
    """How the model should shape its final answer."""
    TEXT = "text"
    JSON = "json_object"


@dataclass(frozen=True)
class LLMConfig:
    """LLM configuration, read from settings in the composition root."""
    model_name: str
    model_provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_base: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None


@runtime_checkable
class AgentEngine(Protocol):
    """Port for a single-agent runtime (one "turn").

    Given a ready ``conversation`` (system prompt + prior messages + the new
    user turn already appended) and the available ``tools``, an engine runs the
    full model + tool-call loop, **appends every message it produces to
    ``conversation`` in place**, and streams framework-neutral domain events.

    The caller owns persistence: it simply saves ``conversation`` as it iterates
    the stream. Swapping the underlying agent framework means providing another
    adapter that implements this Protocol; ``PlanActFlow`` never changes.
    """

    def run(
        self,
        conversation: Memory,
        *,
        tools: Sequence[ToolSpec] = (),
        response_format: ResponseFormat = ResponseFormat.TEXT,
        allow_tools: bool = True,
    ) -> AsyncIterator[AgentEvent]:
        ...
