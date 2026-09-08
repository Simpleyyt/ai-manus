"""Resolve skill instruction bodies for agent prompt injection."""

from app.application.data.official_skill_packages import read_official_skill_md
from app.domain.models.skill import Skill, SkillOwnerType
from app.domain.skills.skill_md import parse_skill_md


def resolve_skill_body(skill: Skill) -> str:
    """Return the instruction body injected into the agent system prompt."""
    if skill.owner_type == SkillOwnerType.OFFICIAL:
        official_skill_md = read_official_skill_md(skill.name)
        if official_skill_md:
            official_body = parse_skill_md(official_skill_md).body
            if official_body:
                return official_body

    if skill.body and skill.body.strip():
        return skill.body.strip()

    description = (skill.description or "").strip()
    if description:
        return description

    return f"Execute the {skill.name} skill."
