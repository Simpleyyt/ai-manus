"""Skill markdown parsing utilities."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Optional

_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)
_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ParsedSkillMd:
    name: str
    description: str
    body: str


def parse_skill_md(content: str) -> ParsedSkillMd:
    """Parse SKILL.md with optional YAML frontmatter into metadata + body."""
    text = (content or "").strip()
    if not text:
        return ParsedSkillMd(name="", description="", body="")

    frontmatter: dict[str, str] = {}
    body = text
    match = _FRONTMATTER_PATTERN.match(text)
    if match:
        frontmatter = _parse_frontmatter_block(match.group(1))
        body = match.group(2).strip()

    name = _normalize_skill_name(frontmatter.get("name", ""))
    description = (frontmatter.get("description") or "").strip()
    if not description and body:
        first_line = body.splitlines()[0].lstrip("#").strip()
        description = first_line or description

    return ParsedSkillMd(name=name, description=description, body=body)


def extract_skill_md_from_bytes(data: bytes, filename: str = "") -> str:
    """Return SKILL.md text from raw markdown or a .zip/.skill archive."""
    if not data:
        raise ValueError("Empty skill package")

    lowered = filename.lower()
    if lowered.endswith(".md") or _looks_like_markdown(data):
        return data.decode("utf-8")

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.namelist():
            if member.rstrip("/").endswith("SKILL.md"):
                return archive.read(member).decode("utf-8")

    raise ValueError("SKILL.md not found at archive root")


def _parse_frontmatter_block(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    current_key: Optional[str] = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is None:
            return
        values[current_key] = "\n".join(current_lines).strip()
        current_key = None
        current_lines = []

    for raw_line in block.splitlines():
        if not raw_line.strip():
            if current_key is not None:
                current_lines.append("")
            continue

        if ":" in raw_line and not raw_line.startswith(" "):
            flush()
            key, _, value = raw_line.partition(":")
            current_key = key.strip()
            marker = value.strip()
            if marker in {">", ">-", "|", "|-"}:
                current_lines = []
            else:
                current_lines = [marker.strip().strip('"').strip("'")]
            continue

        if current_key is not None:
            current_lines.append(raw_line.strip())

    flush()
    return values


def _looks_like_markdown(data: bytes) -> bool:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    stripped = text.lstrip("\ufeff").strip()
    return stripped.startswith("---") or stripped.startswith("#")


def _normalize_skill_name(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if not normalized or not _SKILL_NAME_PATTERN.fullmatch(normalized):
        return ""
    return normalized
