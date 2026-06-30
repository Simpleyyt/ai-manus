"""Framework-agnostic tool layer.

Replaces LangChain's ``@tool`` / ``BaseTool`` / ``BaseToolkit`` with a small
domain-owned equivalent so the domain layer carries no framework dependency.

- ``@tool`` marks an (async) toolkit method as a callable tool.
- ``Tool`` wraps one callable: it exposes an OpenAI function schema
  (``to_schema()``) for the LLM and an ``invoke(args)`` coroutine for execution.
- ``BaseToolkit`` collects the decorated methods of a subclass into ``Tool``s.
"""
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.domain.services.tools.schema import build_tool_schema

import inspect


def tool(func: Optional[Callable] = None, *, parse_docstring: bool = True, name: Optional[str] = None):
    """Mark a toolkit method as a tool.

    Usable as ``@tool``, ``@tool()`` or ``@tool(parse_docstring=True)``. The
    decorated method stays a normal coroutine; metadata is attached for
    ``BaseToolkit`` to discover.
    """
    def decorator(f: Callable) -> Callable:
        f._tool_meta = {"name": name or f.__name__}
        return f

    if func is not None and callable(func):
        return decorator(func)
    return decorator


class Tool:
    """A single invocable tool with an OpenAI-format schema."""

    def __init__(
        self,
        toolkit: "BaseToolkit",
        name: str,
        schema: Dict[str, Any],
        invoke_fn: Callable[[Dict[str, Any]], Awaitable[Any]],
    ):
        self.toolkit = toolkit
        self.name = name
        self._schema = schema
        self._invoke_fn = invoke_fn

    @property
    def description(self) -> str:
        return self._schema.get("function", {}).get("description", "")

    def to_schema(self) -> Dict[str, Any]:
        """Return the OpenAI function-call schema for this tool."""
        return self._schema

    async def invoke(self, args: Optional[Dict[str, Any]] = None) -> Any:
        """Invoke the tool and return its raw result."""
        return await self._invoke_fn(args or {})


class BaseToolkit:
    """Base toolset class, providing common tool calling methods."""

    name: str = ""

    def __init__(self):
        self.tools: List[Tool] = []
        for _, member in inspect.getmembers(self):
            meta = getattr(member, "_tool_meta", None)
            if not meta:
                continue
            tool_name = meta["name"]
            schema = build_tool_schema(member, tool_name)
            self.tools.append(
                Tool(
                    toolkit=self,
                    name=tool_name,
                    schema=schema,
                    invoke_fn=lambda args, _m=member: _m(**args),
                )
            )

    def get_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return self.tools

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get the tool with the given name, or None."""
        for tool_obj in self.tools:
            if tool_obj.name == tool_name:
                return tool_obj
        return None
