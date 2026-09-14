"""Access repository-bundled official skill packages."""

from pathlib import Path
from typing import Optional


def official_skills_data_root() -> Path:
    """Return the root containing official skill package directories."""
    return Path(__file__).with_name("official_skills")


def official_package_dir(skill_name: str) -> Optional[Path]:
    """Return an official skill package directory when it exists."""
    if not skill_name or Path(skill_name).name != skill_name:
        return None

    package_dir = official_skills_data_root() / skill_name
    if not package_dir.is_dir():
        return None
    return package_dir


def read_official_skill_md(skill_name: str) -> Optional[str]:
    """Read an official package's SKILL.md when available."""
    package_dir = official_package_dir(skill_name)
    if package_dir is None:
        return None

    skill_md = package_dir / "SKILL.md"
    if not skill_md.is_file():
        return None
    return skill_md.read_text(encoding="utf-8")
