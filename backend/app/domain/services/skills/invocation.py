"""Parse /{skill-name} invocations from user chat text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_SKILL_TOKEN = re.compile(
    r"^/(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)(?:\s+(?P<task>[\s\S]*))?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedSkillInvocation:
    name: str
    task: str


def parse_skill_invocation(text: str) -> Optional[ParsedSkillInvocation]:
    """Return skill name + remaining task when message starts with /{name}."""
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return None
    match = _SKILL_TOKEN.match(raw)
    if not match:
        return None
    name = match.group("name").lower()
    task = (match.group("task") or "").strip()
    return ParsedSkillInvocation(name=name, task=task)
