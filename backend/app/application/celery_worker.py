"""Celery worker entry-point.

Start with::

    celery -A app.application.celery_worker worker --loglevel=info

The worker receives a ``session_id`` via *context* and calls
:meth:`AgentService.create_runner` — the **same** code path the API
process uses — so runner construction logic is never duplicated.
"""

import asyncio
import logging

from app.infrastructure.external.task.celery_app import get_celery_app
from app.infrastructure.external.task.celery_task import CeleryTaskProxy

logger = logging.getLogger(__name__)

app = get_celery_app()

# ---------------------------------------------------------------------------
# One-time infrastructure bootstrap for the worker process
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
    await _ensure_infrastructure()

    from app.interfaces.dependencies import get_agent_service

    session_id = context.get("session_id", "")
    service = get_agent_service()
    runner = await service.create_runner(session_id)

    proxy = CeleryTaskProxy(task_id)
    try:
        await runner.run(proxy)
    except Exception:
        logger.exception("Task %s failed", task_id)
    finally:
        await runner.on_done(proxy)


@app.task(name="manus.execute_agent_task", bind=True)
def execute_agent_task(self, task_id: str, context: dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute(task_id, context))
    finally:
        loop.close()
