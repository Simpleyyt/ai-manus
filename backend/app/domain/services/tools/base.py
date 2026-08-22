"""Framework-agnostic tool abstraction for the domain layer.

Tools are written as classes — ``name``, ``description``, a Pydantic
``Args`` / ``args_schema``, and ``run`` — matching the usual structured-tool
shape without depending on LangChain. ``Tool`` / ``BaseToolkit`` expose them
to the agent loop and the LLM gateway.

Two additional concepts support modern context engineering:

* ``Tool.dynamic`` — build an invocable tool from a runtime schema and an
  async invoker (used for MCP tools discovered at runtime), so every tool the
  LLM sees is dispatchable through the same ``BaseToolkit.get_tool`` path.
* ``OutputTool`` — a schema-only tool the model calls to submit structured
  output (plans, step reports, final results). It is never executed; the agent
  loop validates the arguments against a Pydantic model and feeds validation
  errors back to the model for self-repair. This replaces the legacy
  "JSON-in-prompt + repair parser" protocol with native function calling.
"""
import copy
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Type

from pydantic import BaseModel, ValidationError


def _clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Strip pydantic-only ``title`` keys to keep the function schema tidy."""
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        if isinstance(prop, dict):
            prop.pop("title", None)
    for definition in schema.get("$defs", {}).values():
        if isinstance(definition, dict):
            definition.pop("title", None)
            for prop in definition.get("properties", {}).values():
                if isinstance(prop, dict):
                    prop.pop("title", None)
    return schema


# Official Manus timeline shows tool ``brief`` (NL intent), not file paths.
BRIEF_PARAM_SCHEMA: Dict[str, Any] = {
    "type": "string",
    "description": (
        "Short user-facing description of this action in the user's language "
        "(what you are doing), e.g. '编写 Python 示例代码' or 'Run the example "
        "and capture output'. Do not put file paths or raw shell commands here."
    ),
}


def with_brief_parameter(parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Copy an OpenAI parameters schema and require a ``brief`` property.

    Mirrors official Manus ``toolUsed.brief``: the model must supply a
    user-facing NL label; the timeline prefers it over file paths / commands.
    """
    params: Dict[str, Any] = copy.deepcopy(parameters) if parameters else {
        "type": "object",
        "properties": {},
    }
    if params.get("type") != "object":
        params["type"] = "object"
    props = params.setdefault("properties", {})
    if not isinstance(props, dict):
        props = {}
        params["properties"] = props
    if "brief" not in props:
        props["brief"] = dict(BRIEF_PARAM_SCHEMA)
    required = params.setdefault("required", [])
    if isinstance(required, list) and "brief" not in required:
        required.append("brief")
    return params


def take_brief(args: Optional[Dict[str, Any]]) -> tuple[Optional[str], Dict[str, Any]]:
    """Split ``brief`` from tool-call args (brief is UI-only, not for tool impl)."""
    clean = dict(args or {})
    raw = clean.pop("brief", None)
    if raw is None:
        return None, clean
    if isinstance(raw, str):
        text = raw.strip()
        return (text or None), clean
    text = str(raw).strip()
    return (text or None), clean


def _nested_args_schema(cls: Type["Tool"]) -> Optional[Type[BaseModel]]:
    """Return a nested ``Args`` model declared on ``cls``, if any."""
    nested = cls.__dict__.get("Args")
    if isinstance(nested, type) and issubclass(nested, BaseModel):
        return nested
    return None


class Tool:
    """An invocable tool bound to its owning toolkit.

    Subclass and set ``name`` / ``description``, declare arguments as a nested
    ``Args`` Pydantic model (or ``args_schema``), and implement ``run``.
    Runtime-discovered tools (MCP) are built with :meth:`dynamic` instead.
    """

    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("args_schema") is None:
            nested = _nested_args_schema(cls)
            if nested is not None:
                cls.args_schema = nested

    def __init__(
        self,
        *,
        toolkit: Optional["BaseToolkit"] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        invoker: Optional[Callable[[Dict[str, Any]], Awaitable[Any]]] = None,
        args_schema: Optional[Type[BaseModel]] = None,
    ):
        self.toolkit = toolkit
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if args_schema is not None:
            self.args_schema = args_schema
        self._invoker = invoker
        if parameters is not None:
            self.parameters = parameters
        elif self.args_schema is not None:
            self.parameters = _clean_schema(self.args_schema.model_json_schema())
        else:
            self.parameters = {"type": "object", "properties": {}}

    @classmethod
    def dynamic(
        cls,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        invoker: Callable[[Dict[str, Any]], Awaitable[Any]],
        toolkit: "BaseToolkit",
    ) -> "Tool":
        """Build a tool from a runtime-discovered schema (e.g. an MCP tool)."""
        return cls(
            name=name,
            description=description,
            parameters=parameters,
            invoker=invoker,
            toolkit=toolkit,
        )

    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool implementation. Subclasses override this."""
        raise NotImplementedError(f"{type(self).__name__} must implement run()")

    async def invoke(self, args: Dict[str, Any]) -> Any:
        """Invoke the tool, stripping UI-only ``brief`` and validating args."""
        _, clean = take_brief(args)
        if self._invoker is not None:
            return await self._invoker(clean)
        if self.args_schema is not None:
            validated = self.args_schema.model_validate(clean)
            return await self.run(**validated.model_dump())
        return await self.run(**clean)

    def to_openai_schema(self) -> Dict[str, Any]:
        """Render this tool as an OpenAI function-calling schema."""
        # Soft chat/plan tools are not StandardToolUsed rows — no brief.
        toolkit_name = getattr(self.toolkit, "name", "") or ""
        parameters = (
            self.parameters
            if toolkit_name in {"message", "todo"}
            else with_brief_parameter(self.parameters)
        )
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }


class OutputTool:
    """A schema-only tool the model calls to submit structured output.

    The agent loop never executes it; instead the arguments are validated
    against ``schema`` and returned as the structured result of the run.
    Validation errors are sent back to the model as the tool response so it
    can correct itself — native function calling replaces prompt-embedded
    JSON format instructions.
    """

    def __init__(self, name: str, description: str, schema: Type[BaseModel]):
        self.name = name
        self.description = description
        self.schema = schema
        self.parameters = _clean_schema(schema.model_json_schema())

    def validate(self, args: Dict[str, Any]) -> BaseModel:
        """Validate raw tool-call arguments against the output schema.

        Raises:
            pydantic.ValidationError: when the arguments do not conform.
        """
        return self.schema.model_validate(args or {})

    def to_openai_schema(self) -> Dict[str, Any]:
        """Render this output tool as an OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class BaseToolkit:
    """Base toolset class, providing common tool discovery and lookup.

    Subclasses set ``tool_types`` to the :class:`Tool` classes they expose.
    They may also set ``instructions`` — usage guidance assembled into the
    system prompt only when the toolkit is actually bound to the agent,
    keeping prompt content and available tools in sync.
    """

    name: str = ""
    instructions: str = ""
    tool_types: Sequence[Type[Tool]] = ()

    def __init__(self):
        self.tools: List[Tool] = [cls(toolkit=self) for cls in type(self).tool_types]

    def get_tools(self) -> List[Tool]:
        """Return all invocable tools in this toolkit."""
        return self.tools

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI function schemas for all tools in this toolkit."""
        return [t.to_openai_schema() for t in self.get_tools()]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Return the tool with the given name, or ``None``."""
        for t in self.get_tools():
            if t.name == tool_name:
                return t
        return None


def describe_toolkits(toolkits: List[BaseToolkit]) -> str:
    """Render a compact capability overview of the given toolkits.

    Used to inform the planner about available capabilities without paying
    the context cost of full function schemas.
    """
    lines: List[str] = []
    for toolkit in toolkits:
        tool_names = [t.name for t in toolkit.get_tools()]
        if not tool_names:
            continue
        lines.append(f"- {toolkit.name}: {', '.join(tool_names)}")
    return "\n".join(lines)


__all__ = [
    "Tool",
    "OutputTool",
    "BaseToolkit",
    "describe_toolkits",
    "ValidationError",
]
