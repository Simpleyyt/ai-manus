"""Shared location for operator-edited Apps and official skills."""

import os
from pathlib import Path

from app.core.config import get_settings

# Docker Compose mounts the repo-root config/ directory here.
OPERATOR_CONFIG_MOUNT = "/etc/ai-manus"


def default_operator_config_dir() -> Path:
    """Directory that holds connectors.json and skills/ together.

    ``CONFIG_DIR`` wins. Otherwise use ``/etc/ai-manus`` when it is mounted,
    then the repo-root ``config/`` directory.
    """
    configured = os.environ.get("CONFIG_DIR", "").strip()
    if not configured:
        configured = (get_settings().config_dir or "").strip()
    if configured:
        return Path(configured)
    if os.path.isdir(OPERATOR_CONFIG_MOUNT):
        return Path(OPERATOR_CONFIG_MOUNT)
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "config"
