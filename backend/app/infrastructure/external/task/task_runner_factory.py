"""Concrete TaskRunner factory for Celery workers.

This module is the single assembly point that knows about specific
infrastructure implementations (DockerSandbox, Mongo repositories, etc.).
It is imported by the Celery worker at startup and registered via
``CeleryTask.set_runner_factory()``, keeping ``celery_task.py`` free of
any concrete dependency.
"""

import logging
from typing import Optional

from app.domain.external.task import TaskRunner

logger = logging.getLogger(__name__)

_infrastructure_ready = False


async def _ensure_infrastructure() -> None:
    """Initialise MongoDB / Beanie / Redis once per worker process."""
    global _infrastructure_ready
    if _infrastructure_ready:
        return

    from app.core.config import get_settings
    from app.infrastructure.storage.mongodb import get_mongodb
    from app.infrastructure.storage.redis import get_redis
    from app.infrastructure.models.documents import (
        AgentDocument,
        SessionDocument,
        UserDocument,
    )
    from beanie import init_beanie

    settings = get_settings()
    await get_mongodb().initialize()
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument],
    )
    await get_redis().initialize()
    _infrastructure_ready = True
    logger.info("Worker infrastructure initialised")


async def create_runner_from_context(context: dict) -> TaskRunner:
    """Create an ``AgentTaskRunner`` inside a Celery worker from *context*.

    *context* is the dict returned by ``AgentTaskRunner.get_context()`` and
    contains only primitive, JSON-serialisable values.
    """
    from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
    from app.infrastructure.external.file.gridfsfile import get_file_storage
    from app.infrastructure.external.search import get_search_engine
    from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
    from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
    from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
    from app.domain.services.agent_task_runner import AgentTaskRunner

    await _ensure_infrastructure()

    sandbox_id = context["sandbox_id"]
    sandbox = await DockerSandbox.get(sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {sandbox_id} not found")

    browser = await sandbox.get_browser()
    if not browser:
        raise RuntimeError(f"Browser unavailable for sandbox {sandbox_id}")

    return AgentTaskRunner(
        session_id=context["session_id"],
        agent_id=context["agent_id"],
        user_id=context["user_id"],
        sandbox=sandbox,
        browser=browser,
        agent_repository=MongoAgentRepository(),
        session_repository=MongoSessionRepository(),
        file_storage=get_file_storage(),
        mcp_repository=FileMCPRepository(),
        search_engine=get_search_engine(),
    )
