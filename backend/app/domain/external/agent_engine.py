from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from app.domain.models.event import BaseEvent
from app.domain.models.memory import Memory
from app.domain.models.tool_spec import ToolSpec


@dataclass
class LLMConfig:
    """Framework-neutral LLM configuration.

    Read from settings in the composition root and injected into the engine, so
    the domain never reads global configuration itself.
    """
    model_name: str
    model_provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_base: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None


@dataclass
class AgentRunRequest:
    """Everything an engine needs to run a single agent turn.

    ``memory`` is the working conversation; the engine appends every message it
    produces (assistant + tool results) to it in place. ``on_progress`` is an
    optional persistence hook the engine invokes after each memory mutation so
    durability/resume semantics can be preserved by the caller without coupling
    the engine to a repository.
    """
    system_prompt: str
    memory: Memory
    user_input: str
    tools: List[ToolSpec] = field(default_factory=list)
    response_format: Optional[str] = None
    tool_choice: Optional[str] = None
    max_iterations: int = 100
    max_retries: int = 3
    retry_interval: float = 1.0
    on_progress: Optional[Callable[[], Awaitable[None]]] = None


@runtime_checkable
class AgentEngine(Protocol):
    """Port for a single-agent runtime (one "turn").

    Given a system prompt, prior conversation (memory), the new user input, and
    the available tools, an engine runs the full model + tool-call loop
    internally, appends every produced message to ``request.memory``, and
    streams framework-neutral domain events (``ToolEvent`` / ``MessageEvent`` /
    ``ErrorEvent``). The final ``MessageEvent`` carries the assistant's final
    content.

    The plan-act orchestration (:class:`PlanActFlow`) and the planner/executor
    agents stay in the domain and are unaware of which concrete engine runs a
    turn, so swapping the underlying agent framework only means providing a new
    adapter that implements this Protocol.
    """

    async def run(self, request: AgentRunRequest) -> AsyncGenerator[BaseEvent, None]:
        ...
