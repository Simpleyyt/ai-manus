#!/usr/bin/env python3
"""Generate README / Docsify demo markdown from docs/demos.yml.

Looks for tags in markdown files:

  <!-- demos:readme:en -->
  ... auto-generated ...
  <!-- /demos:readme:en -->

  <!-- demos:docsify:zh -->
  ...
  <!-- /demos:docsify:zh -->

Supported targets: readme|docsify × en|zh
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DEMOS_FILE = ROOT / "docs" / "demos.yml"

# Files that may contain demo sync tags
TARGET_FILES = [
    ROOT / "README.md",
    ROOT / "README_zh.md",
    ROOT / "docs" / "demo.md",
    ROOT / "docs" / "en" / "demo.md",
]

TAG_RE = re.compile(
    r"<!--\s*demos:(readme|docsify):(en|zh)\s*-->\s*\n.*?<!--\s*/demos:\1:\2\s*-->",
    re.DOTALL,
)


def pick(item: dict, key: str, lang: str) -> str | None:
    """Prefer lang-specific field (url_en / title_zh), else shared field."""
    specific = item.get(f"{key}_{lang}")
    if specific:
        return str(specific)
    shared = item.get(key)
    return str(shared) if shared else None


def render_readme(items: list[dict], lang: str) -> str:
    lines: list[str] = []
    task_label = "Task" if lang == "en" else "任务"
    for item in items:
        title = pick(item, "title", lang) or item.get("id", "Demo")
        url = pick(item, "url", lang)
        task = pick(item, "task", lang)
        lines.append(f"### {title}")
        lines.append("")
        if task:
            lines.append(f"* {task_label}: {task}")
            lines.append("")
        if url:
            # Match historical README style: bare URL or <url>
            if lang == "en" and item.get("id") != "basic":
                lines.append(f"<{url}>")
            else:
                lines.append(url)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_docsify(items: list[dict], lang: str) -> str:
    lines: list[str] = []
    task_prefix = "Task" if lang == "en" else "任务"
    for item in items:
        title = pick(item, "title", lang) or item.get("id", "Demo")
        url = pick(item, "url", lang)
        task = pick(item, "task", lang)
        lines.append(f"## {title}")
        lines.append("")
        if task:
            lines.append(f"> {task_prefix}: {task}" if lang == "en" else f"> {task_prefix}: {task}")
            # Chinese historically used "任务: " without space inconsistency — keep simple
            if lang == "zh":
                lines[-1] = f"> 任务: {task}"
            else:
                lines[-1] = f"> Task: {task}"
            lines.append("")
        if url:
            # Docsify video embed
            lines.append(f"[]({url} ':include controls width=\"100%\"')")
            lines.append("")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render(section: str, lang: str, data: dict) -> str:
    items = data.get(section) or []
    if section == "readme":
        return render_readme(items, lang)
    if section == "docsify":
        return render_docsify(items, lang)
    raise ValueError(f"unknown section: {section}")


def sync_file(path: Path, data: dict) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = False

    def repl(match: re.Match[str]) -> str:
        nonlocal updated
        section, lang = match.group(1), match.group(2)
        body = render(section, lang, data)
        updated = True
        return f"<!-- demos:{section}:{lang} -->\n{body}<!-- /demos:{section}:{lang} -->"

    new_text, n = TAG_RE.subn(repl, text)
    if n and new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"Updated {path.relative_to(ROOT)} ({n} block(s))")
        return True
    if n == 0:
        return False
    print(f"Unchanged {path.relative_to(ROOT)}")
    return False


def main() -> int:
    if not DEMOS_FILE.exists():
        print(f"Missing {DEMOS_FILE}", file=sys.stderr)
        return 1
    data = yaml.safe_load(DEMOS_FILE.read_text(encoding="utf-8")) or {}
    any_updated = False
    for path in TARGET_FILES:
        if sync_file(path, data):
            any_updated = True
    if not any_updated:
        print("No demo sync tags found or content already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
