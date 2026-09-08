"""Skill toolkit — progressive disclosure via ``load_skill`` tool."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, tool
from app.domain.skills.package import skill_md_path

SkillPair = Tuple[str, str]
BodyResolver = Callable[[str], Optional[str]]


class SkillToolkit(BaseToolkit):
    """Expose ``load_skill`` so L2 instructions enter context via a tool result.

    Catalog (L1) is embedded in the tool description (Claude Code / Agent Skills
    style). Full SKILL.md body is returned only when the model calls the tool.
    """

    name: str = "skill"
    instructions: str = """
- When a skill is relevant (or the user invoked `/{name}` / a skill chip), call
  `load_skill` with that skill's name before other work
- Follow the returned skill instructions; do not invent skill behavior from the
  short catalog description alone
- Do not call `load_skill` for a skill that is not listed in <available_skills>
- After loading, use file/shell tools for scripts or references under the skill
  package directory only when the instructions say so
"""

    def __init__(
        self,
        skills: Optional[List[SkillPair]] = None,
        bodies: Optional[Dict[str, str]] = None,
        body_resolver: Optional[BodyResolver] = None,
    ):
        super().__init__()
        self._skills: List[SkillPair] = list(skills or [])
        self._bodies: Dict[str, str] = dict(bodies or {})
        self._body_resolver = body_resolver

    def set_skills(self, skills: List[SkillPair]) -> None:
        self._skills = list(skills or [])

    def set_bodies(self, bodies: Dict[str, str]) -> None:
        self._bodies = dict(bodies or {})

    def _enabled_names(self) -> set[str]:
        return {name for name, _ in self._skills}

    def _resolve_body(self, name: str) -> str:
        if name in self._bodies and (self._bodies[name] or "").strip():
            return self._bodies[name].strip()
        if self._body_resolver:
            resolved = self._body_resolver(name)
            if resolved and resolved.strip():
                return resolved.strip()
        return ""

    def _catalog_xml(self) -> str:
        if not self._skills:
            return "<available_skills>\n(none enabled)\n</available_skills>"
        lines = ["<available_skills>"]
        for name, description in self._skills:
            desc = (description or "").strip().replace("\n", " ")
            lines.append(f"<skill><name>{name}</name><description>{desc}</description></skill>")
        lines.append("</available_skills>")
        return "\n".join(lines)

    def _load_skill_description(self) -> str:
        return (
            "Load a skill's full SKILL.md instructions into context. "
            "When users ask you to perform tasks, check if any of the available "
            "skills below can help complete the task more effectively. Skills "
            "provide specialized workflows and must be loaded before following "
            "them.\n\n"
            "Rules:\n"
            "- Only load skills listed in <available_skills> below\n"
            "- Invoke with the skill name only (no path, no arguments)\n"
            "- Prefer load_skill over inventing a workflow from the short description\n"
            "- After loading, follow the returned instructions (and optional "
            "scripts/assets under the skill package)\n\n"
            f"{self._catalog_xml()}"
        )

    def get_tool_schemas(self) -> List[dict]:
        schemas = super().get_tool_schemas()
        for schema in schemas:
            fn = schema.get("function") or {}
            if fn.get("name") == "load_skill":
                fn["description"] = self._load_skill_description()
        return schemas

    @tool(parse_docstring=True)
    async def load_skill(self, name: str) -> ToolResult:
        """Load full instructions for an enabled skill by name.

        Args:
            name: Skill name from <available_skills> (e.g. "pdf"), without slash
        """
        skill_name = (name or "").strip().lstrip("/")
        if not skill_name:
            return ToolResult(success=False, message="Skill name is required")
        if skill_name not in self._enabled_names():
            return ToolResult(
                success=False,
                message=f"Unknown or disabled skill: {skill_name}",
            )
        body = self._resolve_body(skill_name)
        if not body:
            return ToolResult(
                success=False,
                message=f"Skill {skill_name} has empty instructions",
            )
        path = skill_md_path(skill_name)
        content = (
            f"[Skill loaded: /{skill_name}]\n"
            f"Package path: `{path.rsplit('/', 1)[0]}/`\n\n"
            f"{body}"
        )
        return ToolResult(
            success=True,
            data={
                "name": skill_name,
                "file": path,
                "content": content,
            },
        )
