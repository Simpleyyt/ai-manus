"""Framework-agnostic tool abstraction for the domain layer.

Replaces the previous LangChain ``BaseTool`` / ``@tool`` integration so the
domain no longer depends on LangChain. A lightweight ``@tool`` decorator parses
the method signature and its Google-style docstring into an OpenAI-compatible
function schema, and ``Tool`` / ``BaseToolkit`` expose the tools for the agent
loop and the LLM gateway.
"""
import inspect
import re
from typing import Any, Callable, Dict, List, Optional, get_type_hints

from pydantic import Field, create_model


def _parse_docstring(doc: Optional[str]) -> tuple[str, Dict[str, str]]:
    """Split a Google-style docstring into (summary, {param: description})."""
    if not doc:
        return "", {}

    lines = doc.strip("\n").split("\n")
    summary_lines: List[str] = []
    param_docs: Dict[str, str] = {}
    in_args = False
    current: Optional[str] = None

    for raw in lines:
        line = raw.strip()
        if re.match(r"^(Args|Arguments|Parameters)\s*:\s*$", line):
            in_args = True
            current = None
            continue
        if in_args and re.match(r"^(Returns?|Raises?|Yields?|Examples?|Note)\s*:", line):
            in_args = False
            current = None
            continue
        if in_args:
            m = re.match(r"^(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)$", line)
            if m:
                current = m.group(1)
                param_docs[current] = m.group(2).strip()
            elif current and line:
                param_docs[current] += " " + line
        else:
            summary_lines.append(line)

    summary = " ".join(s for s in summary_lines if s).strip()
    return summary, param_docs


def _clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Strip pydantic-only ``title`` keys to keep the function schema tidy."""
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        if isinstance(prop, dict):
            prop.pop("title", None)
    for definition in schema.get("$defs", {}).values():
        if isinstance(definition, dict):
            definition.pop("title", None)
    return schema


def _build_parameters(func: Callable, param_docs: Dict[str, str]) -> Dict[str, Any]:
    """Derive an OpenAI ``parameters`` JSON schema from a function signature."""
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    fields: Dict[str, Any] = {}
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        annotation = hints.get(pname, str)
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[pname] = (annotation, Field(default, description=param_docs.get(pname)))

    model = create_model(f"{func.__name__}Args", **fields)
    return _clean_schema(model.model_json_schema())


class ToolFunction:
    """Marker produced by ``@tool``; collected by ``BaseToolkit`` at init."""

    def __init__(self, func: Callable, name: str, description: str, parameters: Dict[str, Any]):
        self.func = func
        self.name = name
        self.description = description
        self.parameters = parameters


def tool(func: Optional[Callable] = None, **_kwargs: Any):
    """Decorator that turns an async method into a :class:`ToolFunction`.

    Accepts and ignores extra keyword arguments (e.g. ``parse_docstring``) for
    drop-in compatibility with the previous LangChain decorator call sites.
    """

    def decorator(f: Callable) -> ToolFunction:
        summary, param_docs = _parse_docstring(f.__doc__)
        parameters = _build_parameters(f, param_docs)
        return ToolFunction(
            func=f,
            name=f.__name__,
            description=summary,
            parameters=parameters,
        )

    if callable(func):
        return decorator(func)
    return decorator


class Tool:
    """An invocable tool bound to its owning toolkit."""

    def __init__(self, tool_function: ToolFunction, toolkit: "BaseToolkit"):
        self._func = tool_function.func
        self.name = tool_function.name
        self.description = tool_function.description
        self.parameters = tool_function.parameters
        self.toolkit = toolkit

    async def invoke(self, args: Dict[str, Any]) -> Any:
        """Invoke the underlying coroutine with the given arguments."""
        return await self._func(self.toolkit, **(args or {}))

    def to_openai_schema(self) -> Dict[str, Any]:
        """Render this tool as an OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class BaseToolkit:
    """Base toolset class, providing common tool discovery and lookup."""

    name: str = ""

    def __init__(self):
        self.tools: List[Tool] = []
        for _, member in inspect.getmembers(
            type(self), lambda x: isinstance(x, ToolFunction)
        ):
            self.tools.append(Tool(member, toolkit=self))

    def get_tools(self) -> List[Tool]:
        """Return all invocable tools in this toolkit."""
        return self.tools

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI function schemas for all tools in this toolkit."""
        return [t.to_openai_schema() for t in self.tools]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Return the tool with the given name, or ``None``."""
        for t in self.tools:
            if t.name == tool_name:
                return t
        return None
