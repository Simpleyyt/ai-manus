"""Access operator-edited official skill packages."""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional

from app.core.config import get_settings
from app.core.operator_config import default_operator_config_dir

logger = logging.getLogger(__name__)

_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def official_skills_data_root() -> Path:
    """Resolve the directory of official skill packages.

    ``SKILLS_PATH`` wins. Otherwise use ``skills/`` inside the shared operator
    config directory (``CONFIG_DIR``, else ``/etc/ai-manus``, else repo-root
    ``config/``).
    """
    configured = os.environ.get("SKILLS_PATH", "").strip()
    if not configured:
        configured = (get_settings().skills_path or "").strip()
    if configured:
        return Path(configured)
    return default_operator_config_dir() / "skills"


def iter_official_package_dirs() -> List[Path]:
    """Return skill package directories that contain a SKILL.md, sorted by name."""
    root = official_skills_data_root()
    if not root.is_dir():
        logger.info("Skills directory not found: %s", root)
        return []

    packages: List[Path] = []
    for child in sorted(root.iterdir(), key=lambda path: path.name):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not _SKILL_NAME_PATTERN.fullmatch(child.name):
            logger.warning(
                "Skipping skill directory %s: name must be lowercase letters, digits, and hyphens",
                child.name,
            )
            continue
        if not (child / "SKILL.md").is_file():
            logger.warning("Skipping skill directory %s: missing SKILL.md", child.name)
            continue
        packages.append(child)
    return packages


def official_package_dir(skill_name: str) -> Optional[Path]:
    """Return an official skill package directory when it exists."""
    if not skill_name or not _SKILL_NAME_PATTERN.fullmatch(skill_name):
        return None

    package_dir = official_skills_data_root() / skill_name
    if not package_dir.is_dir() or not (package_dir / "SKILL.md").is_file():
        return None
    return package_dir


def read_official_skill_md(skill_name: str) -> Optional[str]:
    """Read an official package's SKILL.md when available."""
    package_dir = official_package_dir(skill_name)
    if package_dir is None:
        return None

    skill_md = package_dir / "SKILL.md"
    return skill_md.read_text(encoding="utf-8")
