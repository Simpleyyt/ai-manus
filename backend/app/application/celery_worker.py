"""Celery worker entry-point — application-layer task definitions.

Start the worker with::

    celery -A app.application.celery_worker worker --loglevel=info

This module registers concrete Celery task functions that know how to
build an ``AgentTaskRunner`` and execute it.  All upper-layer wiring
(DockerSandbox, Mongo repositories, …) is intentionally here, keeping
the task *infrastructure* layer (``celery_task.py``) free of any
concrete dependency.
"""

import asyncio
import logging

from app.infrastructure.external.task.celery_app import get_celery_app
from app.infrastructure.external.task.celery_task import CeleryTaskProxy

logger = logging.getLogger(__name__)

app = get_celery_app()

# ---------------------------------------------------------------------------
# One-time infrastructure bootstrap (MongoDB / Beanie / Redis)
# ---------------------------------------------------------------------------

_infra_ready = False


async def _ensure_infrastructure() -> None:
    global _infra_ready
    if _infra_ready:
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
    _infra_ready = True
    logger.info("Celery worker infrastructure initialised")


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

async def _execute(task_id: str, context: dict) -> None:
    from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
    from app.infrastructure.external.file.gridfsfile import get_file_storage
    from app.infrastructure.external.search import get_search_engine
    from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
    from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
    from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
    from app.domain.services.agent_task_runner import AgentTaskRunner
    from app.domain.models.event import ErrorEvent

    await _ensure_infrastructure()

    proxy = CeleryTaskProxy(task_id)

    sandbox_id = context.get("sandbox_id", "")
    sandbox = await DockerSandbox.get(sandbox_id)
    if not sandbox:
        logger.error("Sandbox %s not found for task %s", sandbox_id, task_id)
        await proxy.output_stream.put(
            ErrorEvent(error=f"Sandbox {sandbox_id} not found").model_dump_json()
        )
        return

    browser = await sandbox.get_browser()
    if not browser:
        logger.error("Browser unavailable for sandbox %s", sandbox_id)
        await proxy.output_stream.put(
            ErrorEvent(error="Browser unavailable").model_dump_json()
        )
        return

    runner = AgentTaskRunner(
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

    try:
        await runner.run(proxy)
    except asyncio.CancelledError:
        logger.info("Task %s cancelled", task_id)
    except Exception as e:
        logger.exception("Task %s execution failed", task_id)
        await proxy.output_stream.put(
            ErrorEvent(error=f"Task error: {e}").model_dump_json()
        )
    finally:
        await runner.on_done(proxy)


@app.task(name="manus.execute_agent_task", bind=True)
def execute_agent_task(self, task_id: str, context: dict):
    """Celery task that runs an AgentTaskRunner in a worker process."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute(task_id, context))
    finally:
        loop.close()
