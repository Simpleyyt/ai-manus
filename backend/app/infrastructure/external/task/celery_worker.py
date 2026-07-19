"""Celery worker-side execution of agent tasks.

Each worker process lazily initializes its own event loop, MongoDB/Beanie and
Redis connections, and the AgentTaskRunner factory. The agent coroutine is
supervised by a cancel watcher that polls the Redis cancellation flag set by
``CeleryTask.cancel()`` from any API replica.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from beanie import init_beanie

from app.core.config import get_settings
from app.infrastructure.external.task.celery_app import celery_app, AGENT_TASK_NAME
from app.infrastructure.external.task.celery_task import (
    CeleryTask,
    write_meta,
    clear_cancel,
    is_cancel_requested,
    STATUS_RUNNING,
    STATUS_DONE,
)

logger = logging.getLogger(__name__)

CANCEL_POLL_INTERVAL_SECONDS = 1.0

_loop: Optional[asyncio.AbstractEventLoop] = None
_initialized = False


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get the per-worker-process event loop, creating it lazily after fork."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def _build_runner_factory():
    """Composition root for the worker process (mirrors interfaces/dependencies.py)."""
    from app.domain.services.agent_task_runner import AgentTaskRunnerFactory
    from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
    from app.infrastructure.external.file.gridfsfile import get_file_storage
    from app.infrastructure.external.search import get_search_engine
    from app.infrastructure.external.llm import get_llm
    from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
    from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
    from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository

    return AgentTaskRunnerFactory(
        agent_repository=MongoAgentRepository(),
        session_repository=MongoSessionRepository(),
        sandbox_cls=DockerSandbox,
        file_storage=get_file_storage(),
        mcp_repository=FileMCPRepository(),
        llm=get_llm(),
        search_engine=get_search_engine(),
    )


async def _ensure_initialized() -> None:
    """Initialize MongoDB/Beanie, Redis and the runner factory once per process."""
    global _initialized
    if _initialized:
        return

    from app.infrastructure.storage.mongodb import get_mongodb
    from app.infrastructure.storage.redis import get_redis
    from app.infrastructure.models.documents import (
        AgentDocument,
        SessionDocument,
        UserDocument,
        ClawDocument,
        ProjectDocument,
    )

    settings = get_settings()
    await get_mongodb().initialize()
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument, ClawDocument, ProjectDocument],
    )
    await get_redis().initialize()
    CeleryTask.set_runner_factory(_build_runner_factory())
    _initialized = True
    logger.info("Celery worker process initialized")


async def _watch_cancel(task_id: str, agent_task: asyncio.Task) -> None:
    """Cancel the agent coroutine when the Redis cancellation flag appears."""
    while not agent_task.done():
        if await is_cancel_requested(task_id):
            logger.info(f"Task {task_id} cancel flag detected, cancelling agent coroutine")
            agent_task.cancel()
            return
        await asyncio.sleep(CANCEL_POLL_INTERVAL_SECONDS)


async def _run_agent(task_id: str, params: Dict[str, Any]) -> None:
    await _ensure_initialized()

    runner = await CeleryTask.get_runner_factory().create_runner(params)
    task_handle = CeleryTask(task_id, params=params)

    await write_meta(task_id, STATUS_RUNNING, params)
    agent_task = asyncio.ensure_future(runner.run(task_handle))
    watcher = asyncio.ensure_future(_watch_cancel(task_id, agent_task))
    try:
        # AgentTaskRunner.run handles CancelledError internally (emits a
        # DoneEvent and completes the session); this guard only covers
        # re-raised cancellations from within its exception handler.
        await agent_task
    except asyncio.CancelledError:
        logger.info(f"Task {task_id} agent coroutine cancelled")
    finally:
        watcher.cancel()
        await clear_cancel(task_id)
        await write_meta(task_id, STATUS_DONE, params)
        try:
            await runner.on_done(task_handle)
        except Exception:
            logger.exception(f"Task {task_id} on_done callback failed")


@celery_app.task(name=AGENT_TASK_NAME)
def run_agent_task(task_id: str, params: Dict[str, Any]) -> None:
    """Celery entry point: run one agent task to completion in this process."""
    logger.info(f"Worker picked up agent task {task_id}")
    loop = _get_loop()
    loop.run_until_complete(_run_agent(task_id, params))
    logger.info(f"Worker finished agent task {task_id}")
