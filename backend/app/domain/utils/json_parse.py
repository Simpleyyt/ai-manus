"""Framework-neutral lenient JSON parsing.

Used to turn an assistant's final structured output (produced under a
``json_object`` response format) into a dict, without depending on any agent
framework. Tolerates markdown code fences and leading/trailing prose by falling
back to extracting the outermost JSON object/array.
"""
import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_json_lenient(text: str) -> Any:
    """Parse JSON from ``text``, tolerating fences and surrounding prose.

    Raises:
        ValueError: if no valid JSON object/array can be extracted.
    """
    if text is None:
        raise ValueError("Cannot parse JSON from None")

    candidate = text.strip()

    # Prefer content inside a markdown code fence when present.
    fenced = _FENCE_RE.search(candidate)
    if fenced:
        candidate = fenced.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Fallback: extract the outermost {...} or [...] span.
    extracted = _extract_span(candidate)
    if extracted is not None:
        return json.loads(extracted)

    raise ValueError(f"Failed to parse JSON from output: {text[:200]}")


def _extract_span(text: str) -> str | None:
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not start_candidates:
        return None
    start = min(start_candidates)
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None
