#!/usr/bin/env python3
"""Generate README demo markdown from docs/demos.yml.

Looks for tags in markdown files:

  <!-- demos:readme:en -->
  ... auto-generated ...
  <!-- /demos:readme:en -->

  <!-- demos:readme:zh -->
  ...
  <!-- /demos:readme:zh -->

Supported targets: readme × en|zh

Note: docs/demo.md and docs/en/demo.md are hand-maintained scenario demos
(takeover / file / MCP) and must NOT be synced from this catalog.
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

# Files that may contain demo sync tags (README only — not docs/demo.md)
TARGET_FILES = [
    ROOT / "README.md",
    ROOT / "README_zh.md",
]

TAG_RE = re.compile(
    r"<!--\s*demos:(readme):(en|zh)\s*-->\s*\n.*?<!--\s*/demos:\1:\2\s*-->",
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
        path = pick(item, "path", lang)
        poster = pick(item, "poster", lang)
        task = pick(item, "task", lang)
        lines.append(f"### {title}")
        lines.append("")
        if task:
            lines.append(f"* {task_label}: {task}")
            lines.append("")
        # Native player (Attachments) > poster linking to MP4 > bare MP4 URL
        if url and "user-attachments/assets" in url:
            if lang == "en" and item.get("id") != "basic":
                lines.append(f"<{url}>")
            else:
                lines.append(url)
        elif poster and path:
            lines.append(f"[![{title}]({poster})]({path})")
        elif path:
            if lang == "en" and item.get("id") != "basic":
                lines.append(f"<{path}>")
            else:
                lines.append(path)
        elif url:
            if lang == "en" and item.get("id") != "basic":
                lines.append(f"<{url}>")
            else:
                lines.append(url)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render(section: str, lang: str, data: dict) -> str:
    items = data.get(section) or []
    if section == "readme":
        return render_readme(items, lang)
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
    touched = 0
    for path in TARGET_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if not TAG_RE.search(text):
            continue
        if sync_file(path, data):
            touched += 1
    if touched == 0:
        print("Demo sections already up to date (or no sync tags present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
