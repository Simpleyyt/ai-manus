"""Celery application and the agent-execution task.

The agent flow is async and relies on async MongoDB/Redis clients. Creating a
fresh event loop per Celery task would re-bind those clients to a different loop
each time and is both slow and error prone. Instead every worker process keeps a
single long-lived asyncio event loop running in a background thread; all async
work is submitted onto it via :func:`run_async`.
"""

import asyncio
import logging
import threading
from typing import Optional

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.core.config import get_settings
from app.infrastructure.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

celery_app = Celery(
    "manus",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    # Agent tasks are long-running; only fetch one at a time and ack after
    # completion so a crashed worker re-queues the job.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

# Per-worker-process background event loop.
_loop: Optional[asyncio.AbstractEventLoop] = None
_loop_thread: Optional[threading.Thread] = None


def _start_background_loop() -> None:
    """Start a dedicated asyncio loop running in a daemon thread."""
    global _loop, _loop_thread

    if _loop is not None:
        return

    _loop = asyncio.new_event_loop()

    def _run() -> None:
        asyncio.set_event_loop(_loop)
        _loop.run_forever()

    _loop_thread = threading.Thread(target=_run, name="celery-agent-loop", daemon=True)
    _loop_thread.start()


def run_async(coro):
    """Run ``coro`` on the worker's background event loop and block for it."""
    if _loop is None:
        raise RuntimeError("Worker event loop not initialized")
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()


@worker_process_init.connect
def _on_worker_init(**_kwargs) -> None:
    """Bring up the event loop and storage connections for this worker."""
    from app.infrastructure.storage.bootstrap import init_storage

    _start_background_loop()
    run_async(init_storage())
    logger.info("Celery worker process initialized")


@worker_process_shutdown.connect
def _on_worker_shutdown(**_kwargs) -> None:
    """Tear down storage connections and stop the event loop."""
    from app.infrastructure.storage.bootstrap import shutdown_storage

    try:
        run_async(shutdown_storage())
    except Exception as exc:  # pragma: no cover - best-effort cleanup
        logger.warning(f"Error during worker storage shutdown: {exc}")
    finally:
        if _loop is not None:
            _loop.call_soon_threadsafe(_loop.stop)
    logger.info("Celery worker process shut down")


async def _watch_cancel(task_id: str, run_future: asyncio.Future) -> None:
    """Cancel ``run_future`` when a cancel flag for ``task_id`` is set in Redis."""
    from app.infrastructure.external.task.celery_task import is_cancel_requested

    try:
        while not run_future.done():
            if await is_cancel_requested(task_id):
                logger.info(f"Cancel requested for task {task_id}, cancelling run")
                run_future.cancel()
                return
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass


async def _run_agent_task_async(task_id: str, session_id: str) -> None:
    from app.infrastructure.external.task.agent_runner_factory import (
        create_agent_task_runner,
    )
    from app.infrastructure.external.task.celery_task import (
        CeleryStreamTask,
        clear_cancel_flag,
    )

    runner = await create_agent_task_runner(session_id)
    if runner is None:
        logger.error(f"No runner for session {session_id}; aborting task {task_id}")
        return

    task = CeleryStreamTask(task_id=task_id, session_id=session_id)
    run_future = asyncio.ensure_future(runner.run(task))
    watcher = asyncio.ensure_future(_watch_cancel(task_id, run_future))
    try:
        await run_future
    except asyncio.CancelledError:
        logger.info(f"Task {task_id} run cancelled")
    finally:
        watcher.cancel()
        await clear_cancel_flag(task_id)
        try:
            await runner.on_done(task)
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning(f"Error in on_done for task {task_id}: {exc}")
        # Each worker task builds a fresh runner with its own MCP connections.
        # Release them here (but keep the session's sandbox, which is reused
        # across messages) to avoid leaking connections per task.
        mcp_tool = getattr(runner, "_mcp_tool", None)
        if mcp_tool is not None:
            try:
                await mcp_tool.cleanup()
            except Exception as exc:  # pragma: no cover - best-effort
                logger.warning(f"Error cleaning up MCP for task {task_id}: {exc}")


@celery_app.task(name="app.tasks.run_agent_task")
def run_agent_task(task_id: str, session_id: str) -> None:
    """Celery entry point: execute the agent flow for a session."""
    logger.info(f"Running agent task {task_id} for session {session_id}")
    run_async(_run_agent_task_async(task_id, session_id))
