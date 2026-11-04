"""Official skill catalog loaded from config/skills/."""

import logging
from typing import Dict, List

from app.application.data.official_skill_packages import (
    iter_official_package_dirs,
    read_official_skill_md,
)
from app.domain.models.skill import Skill, SkillOwnerType, SkillSource
from app.domain.skills.skill_md import parse_skill_md

logger = logging.getLogger(__name__)

DEFAULT_PERSONAL_SKILL = {
    "name": "data-viz",
    "description": "Plot CSV data with clear charts",
    "body": (
        "# Data Visualization\n\n"
        "Load the user's CSV, pick appropriate chart types, and save plots to files "
        "with clear labels and legends."
    ),
}


def official_skill_id(name: str) -> str:
    """Stable subscription id for a package directory name."""
    return "skill_" + name.replace("-", "_")


def list_official_skills() -> List[Skill]:
    """Reload official skills from SKILL.md frontmatter on each call."""
    skills: List[Skill] = []
    for package_dir in iter_official_package_dirs():
        content = read_official_skill_md(package_dir.name)
        if not content:
            continue
        parsed = parse_skill_md(content)
        if parsed.name != package_dir.name:
            logger.warning(
                "Skipping skill directory %s: SKILL.md name is %r",
                package_dir.name,
                parsed.name,
            )
            continue
        description = (parsed.description or "").strip()
        if not description:
            logger.warning(
                "Skipping skill directory %s: SKILL.md description is empty",
                package_dir.name,
            )
            continue
        skills.append(
            Skill(
                id=official_skill_id(parsed.name),
                name=parsed.name,
                description=description,
                owner_type=SkillOwnerType.OFFICIAL,
                source=SkillSource.CATALOG,
            )
        )
    return skills


def official_skill_by_id() -> Dict[str, Skill]:
    return {skill.id: skill for skill in list_official_skills()}


def default_added_official_skill_ids() -> List[str]:
    """First visit subscribes every package currently in the skills directory."""
    return [skill.id for skill in list_official_skills()]
