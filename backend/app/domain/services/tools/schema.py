"""Build OpenAI-style function schemas from Python callables.

Framework-agnostic replacement for LangChain's ``@tool(parse_docstring=True)``
schema generation. Reads the function signature (type hints + defaults) and a
Google-style docstring to produce a tool schema in OpenAI function-call format::

    {"type": "function",
     "function": {"name": ..., "description": ..., "parameters": {<json schema>}}}
"""
import inspect
import re
from typing import Any, Dict, List, Tuple, Union, get_args, get_origin, get_type_hints

_PRIMITIVE_JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

_NONE_TYPE = type(None)


def _is_optional(annotation: Any) -> bool:
    """True if the annotation is Optional[...] / Union[..., None]."""
    if get_origin(annotation) is Union:
        return _NONE_TYPE in get_args(annotation)
    return False


def _type_to_schema(annotation: Any) -> Dict[str, Any]:
    """Map a Python type annotation to a JSON schema fragment."""
    if annotation in _PRIMITIVE_JSON_TYPES:
        return {"type": _PRIMITIVE_JSON_TYPES[annotation]}

    origin = get_origin(annotation)

    if origin is Union:
        non_none = [a for a in get_args(annotation) if a is not _NONE_TYPE]
        if len(non_none) == 1:
            return _type_to_schema(non_none[0])
        return {"anyOf": [_type_to_schema(a) for a in non_none]}

    if origin in (list, List):
        args = get_args(annotation)
        item_schema = _type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema}

    if origin in (dict, Dict):
        return {"type": "object"}

    # Unknown / unannotated -> permissive string.
    return {"type": "string"}


def parse_docstring(doc: str) -> Tuple[str, Dict[str, str]]:
    """Parse a Google-style docstring into (description, arg_descriptions)."""
    if not doc:
        return "", {}

    lines = doc.strip().split("\n")
    desc_lines: List[str] = []
    i = 0
    n = len(lines)
    while i < n and lines[i].strip().lower().rstrip(":") not in ("args", "arguments"):
        desc_lines.append(lines[i].strip())
        i += 1
    description = " ".join(line for line in desc_lines if line).strip()

    arg_docs: Dict[str, str] = {}
    if i < n:
        i += 1  # skip the "Args:" line
        arg_pattern = re.compile(r"^(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)$")
        current = None
        for line in lines[i:]:
            stripped = line.strip()
            if not stripped:
                continue
            # Stop at the next docstring section (e.g. "Returns:").
            if stripped.lower().rstrip(":") in ("returns", "raises", "yields", "examples"):
                break
            match = arg_pattern.match(stripped)
            if match:
                current = match.group(1)
                arg_docs[current] = match.group(2).strip()
            elif current:
                arg_docs[current] += " " + stripped

    return description, arg_docs


def build_tool_schema(func: Any, name: str) -> Dict[str, Any]:
    """Build an OpenAI function schema for a (possibly bound) callable."""
    target = func.__func__ if inspect.ismethod(func) else func
    signature = inspect.signature(func)
    try:
        hints = get_type_hints(target)
    except Exception:
        hints = {}

    description, arg_docs = parse_docstring(inspect.getdoc(func))

    properties: Dict[str, Any] = {}
    required: List[str] = []
    for param_name, param in signature.parameters.items():
        if param_name in ("self", "cls"):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        annotation = hints.get(param_name, str)
        param_schema = _type_to_schema(annotation)
        if param_name in arg_docs:
            param_schema = {**param_schema, "description": arg_docs[param_name]}
        properties[param_name] = param_schema

        has_default = param.default is not inspect.Parameter.empty
        if not has_default and not _is_optional(annotation):
            required.append(param_name)

    parameters: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        parameters["required"] = required

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
