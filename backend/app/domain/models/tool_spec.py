from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict


@dataclass
class ToolSpec:
    """Framework-neutral description of a callable tool.

    Carries everything an :class:`~app.domain.external.agent_engine.AgentEngine`
    needs to expose the tool to a model (name, description, JSON-schema
    ``parameters``) and to actually run it (``handler``). Each engine adapter
    translates this into whatever tool type its framework expects.

    ``handler`` receives the parsed arguments dict and returns the raw tool
    result (typically a :class:`~app.domain.models.tool_result.ToolResult`).
    ``toolkit_name`` is surfaced on ``ToolEvent.tool_name`` so the UI can render
    the right rich tool view.
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    toolkit_name: str = ""
