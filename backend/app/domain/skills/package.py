"""Build filesystem skill packages for Sandbox (L3 resources)."""

from __future__ import annotations

from app.domain.models.skill import Skill
from app.domain.skills.body import resolve_skill_body

SKILLS_ROOT = "/home/ubuntu/skills"


def skill_dir(name: str) -> str:
    return f"{SKILLS_ROOT}/{name.strip().lstrip('/')}"


def skill_md_path(name: str) -> str:
    return f"{skill_dir(name)}/SKILL.md"


def build_skill_md_file(skill: Skill) -> str:
    """Serialize a skill into a SKILL.md file (frontmatter + body)."""
    body = resolve_skill_body(skill)
    description = (skill.description or "").strip().replace("\n", " ")
    return (
        "---\n"
        f"name: {skill.name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"{body}\n"
    )
