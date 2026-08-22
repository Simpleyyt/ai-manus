"""Framework-agnostic tool abstraction for the domain layer.

A lightweight ``@tool`` decorator marks toolkit methods. Descriptions come
from **either** ``@tool(...)`` arguments **or** a Google-style docstring,
not a mix. The method stays callable; ``Tool`` / ``BaseToolkit`` expose
the bound tools to the agent loop and the LLM gateway.

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
import inspect
import re
import copy
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, ValidationError, create_model


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


def _normalize_parameters(
    parameters: Dict[str, Any],
    required: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Accept a full JSON schema or a ``{name: {type, description}}`` map."""
    if parameters.get("type") == "object" and "properties" in parameters:
        schema = copy.deepcopy(parameters)
        if required is not None:
            schema["required"] = list(required)
        return _clean_schema(schema)
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": copy.deepcopy(parameters),
    }
    if required is not None:
        schema["required"] = list(required)
    return _clean_schema(schema)


class ToolFunction:
    """Metadata attached by ``@tool``; collected by ``BaseToolkit`` at init."""

    def __init__(self, func: Callable, name: str, description: str, parameters: Dict[str, Any]):
        self.func = func
        self.name = name
        self.description = description
        self.parameters = parameters


def tool(__fn_or_description: Any = None, /, **kwargs: Any):
    """Mark an async toolkit method as an invocable tool.

    Two mutually exclusive ways to supply descriptions:

    * ``@tool`` plus a Google-style docstring (summary + ``Args:``).
    * ``@tool(...)`` with ``description`` / parameter docs — the docstring
      is ignored.

    Parameter types still come from the method signature unless a full
    ``parameters`` schema is passed. The method itself stays callable.
    """

    explicit_name = kwargs.pop("name", None)
    explicit_description = kwargs.pop("description", None)
    explicit_parameters = kwargs.pop("parameters", None)
    explicit_required = kwargs.pop("required", None)
    explicit_args = kwargs.pop("args", None)
    if explicit_args is None:
        explicit_args = {}
    elif not isinstance(explicit_args, dict):
        raise TypeError("@tool args= must be a dict of parameter descriptions")

    extra_param_docs: Dict[str, str] = {}
    for key, value in kwargs.items():
        if not isinstance(value, str):
            raise TypeError(f"@tool {key}= must be a description string")
        extra_param_docs[key] = value

    positional_description = (
        __fn_or_description if isinstance(__fn_or_description, str) else None
    )
    use_decorator_docs = bool(
        positional_description
        or explicit_description
        or explicit_parameters is not None
        or explicit_args
        or extra_param_docs
    )

    def decorate(f: Callable) -> Callable:
        if use_decorator_docs:
            desc = explicit_description or positional_description or ""
            if explicit_parameters is not None:
                parameters = _normalize_parameters(explicit_parameters, explicit_required)
            else:
                parameters = _build_parameters(f, {**explicit_args, **extra_param_docs})
        else:
            desc, param_docs = _parse_docstring(f.__doc__)
            parameters = _build_parameters(f, param_docs)

        f._tool = ToolFunction(
            func=f,
            name=explicit_name or f.__name__,
            description=desc,
            parameters=parameters,
        )
        return f

    if callable(__fn_or_description):
        return decorate(__fn_or_description)
    return decorate


class Tool:
    """An invocable tool bound to its owning toolkit."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        invoker: Callable[[Dict[str, Any]], Awaitable[Any]],
        toolkit: "BaseToolkit",
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.toolkit = toolkit
        self._invoker = invoker

    @classmethod
    def from_function(cls, tool_function: ToolFunction, toolkit: "BaseToolkit") -> "Tool":
        """Build a tool from a ``@tool``-decorated toolkit method."""

        async def invoker(args: Dict[str, Any]) -> Any:
            return await tool_function.func(toolkit, **(args or {}))

        return cls(
            name=tool_function.name,
            description=tool_function.description,
            parameters=tool_function.parameters,
            invoker=invoker,
            toolkit=toolkit,
        )

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

    async def invoke(self, args: Dict[str, Any]) -> Any:
        """Invoke the underlying coroutine with the given arguments."""
        _, clean = take_brief(args)
        return await self._invoker(clean)

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

    Subclasses may set ``instructions`` — usage guidance that is assembled
    into the system prompt only when the toolkit is actually bound to the
    agent, keeping prompt content and available tools in sync.
    """

    name: str = ""
    instructions: str = ""

    def __init__(self):
        self.tools: List[Tool] = []
        for _, member in inspect.getmembers(type(self), inspect.isfunction):
            meta = getattr(member, "_tool", None)
            if isinstance(meta, ToolFunction):
                self.tools.append(Tool.from_function(meta, toolkit=self))

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
    "tool",
    "Tool",
    "ToolFunction",
    "OutputTool",
    "BaseToolkit",
    "describe_toolkits",
    "ValidationError",
]
