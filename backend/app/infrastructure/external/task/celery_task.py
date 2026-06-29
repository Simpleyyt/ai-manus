"""Celery-backed implementation of the :class:`Task` protocol.

A :class:`CeleryStreamTask` looks just like the in-process ``RedisStreamTask``
to the rest of the application — same Redis input/output streams, same
``run``/``cancel``/``done`` surface — but instead of executing the agent flow in
the current process it dispatches it to a Celery worker.

Cross-process state is the crux:

* The agent's events still flow through the per-task Redis streams, so the API
  process reads output exactly as before.
* ``done`` is derived from the Celery result backend (the Celery task id is set
  equal to our task id).
* A ``dispatched`` marker and a ``cancel`` flag live in Redis so the state
  survives across the API process and the worker.
"""

import asyncio
import logging
import uuid
from typing import Optional, Dict

from app.domain.external.task import Task, TaskRunner
from app.infrastructure.external.message_queue.redis_stream_queue import (
    RedisStreamQueue,
    MessageQueue,
)
from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)

# Redis keys for cross-process task control state.
_DISPATCHED_KEY = "task:dispatched:{task_id}"
_CANCEL_KEY = "task:cancel:{task_id}"
# Control flags expire so abandoned tasks don't leak keys.
_CONTROL_TTL_SECONDS = 24 * 60 * 60


async def _mark_dispatched(task_id: str) -> None:
    await get_redis().client.set(
        _DISPATCHED_KEY.format(task_id=task_id), "1", ex=_CONTROL_TTL_SECONDS
    )


async def _is_dispatched(task_id: str) -> bool:
    return bool(await get_redis().client.exists(_DISPATCHED_KEY.format(task_id=task_id)))


async def set_cancel_flag(task_id: str) -> None:
    await get_redis().client.set(
        _CANCEL_KEY.format(task_id=task_id), "1", ex=_CONTROL_TTL_SECONDS
    )


async def is_cancel_requested(task_id: str) -> bool:
    return bool(await get_redis().client.exists(_CANCEL_KEY.format(task_id=task_id)))


async def clear_cancel_flag(task_id: str) -> None:
    await get_redis().client.delete(_CANCEL_KEY.format(task_id=task_id))


def _run_coro_detached(coro) -> None:
    """Run ``coro`` from a sync context.

    If an event loop is already running (the normal case — these calls happen
    inside async FastAPI handlers) the coroutine is scheduled on it as a
    fire-and-forget task. Otherwise it is run to completion.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        loop.create_task(coro)
    else:
        asyncio.run(coro)


class CeleryStreamTask(Task):
    """Task implementation that runs the agent flow on a Celery worker."""

    # Keeps API-process-side handles addressable; worker handles are separate.
    _task_registry: Dict[str, "CeleryStreamTask"] = {}

    def __init__(
        self,
        runner: Optional[TaskRunner] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self._runner = runner
        self._id = task_id or str(uuid.uuid4())
        self._session_id = session_id
        if session_id is None and runner is not None:
            # AgentTaskRunner exposes the session it belongs to.
            self._session_id = getattr(runner, "session_id", None)

        input_stream_name = f"task:input:{self._id}"
        output_stream_name = f"task:output:{self._id}"
        self._input_stream = RedisStreamQueue(input_stream_name)
        self._output_stream = RedisStreamQueue(output_stream_name)

        CeleryStreamTask._task_registry[self._id] = self

    @property
    def id(self) -> str:
        return self._id

    @property
    def done(self) -> bool:
        """Whether the Celery execution has finished.

        Derived from the Celery result backend; the Celery task id equals our
        task id. A never-dispatched task reports ``PENDING`` (not ready), which
        is correct since ``run`` is always invoked right after creation.
        """
        from app.infrastructure.external.task.celery_app import celery_app

        result = celery_app.AsyncResult(self._id)
        return result.ready()

    async def run(self) -> None:
        """Dispatch the agent flow to a Celery worker (once)."""
        from app.infrastructure.external.task.celery_app import run_agent_task

        if await _is_dispatched(self._id):
            # Already running (the worker drains newly-queued input on its own)
            # or already finished — nothing to dispatch.
            logger.debug(f"Task {self._id} already dispatched, skipping")
            return

        if not self._session_id:
            logger.error(f"Cannot dispatch task {self._id}: missing session id")
            return

        await _mark_dispatched(self._id)
        run_agent_task.apply_async(args=[self._id, self._session_id], task_id=self._id)
        logger.info(f"Task {self._id} dispatched to Celery for session {self._session_id}")

    def cancel(self) -> bool:
        """Request cooperative cancellation of the Celery execution."""
        from app.infrastructure.external.task.celery_app import celery_app

        if self.done:
            self._cleanup_registry()
            return False

        # Cooperative cancel: the worker polls this flag and cancels gracefully.
        _run_coro_detached(set_cancel_flag(self._id))
        # Drop the job if it is still queued and has not started yet.
        celery_app.control.revoke(self._id)
        logger.info(f"Task {self._id} cancellation requested")
        self._cleanup_registry()
        return True

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream

    def _cleanup_registry(self) -> None:
        if self._id in CeleryStreamTask._task_registry:
            del CeleryStreamTask._task_registry[self._id]

    @classmethod
    def get(cls, task_id: str) -> Optional["CeleryStreamTask"]:
        """Return a handle to an existing task by id.

        Celery tasks live in worker processes, so a handle is reconstructed
        on demand from the task id (the Redis streams and result backend hold
        all the state that matters).
        """
        existing = cls._task_registry.get(task_id)
        if existing is not None:
            return existing
        return cls(task_id=task_id)

    @classmethod
    def create(cls, runner: TaskRunner) -> "CeleryStreamTask":
        return cls(runner=runner)

    @classmethod
    async def destroy(cls) -> None:
        """No-op for the API process.

        Agent flows execute in Celery workers and own their own lifecycle, so
        the API process does not tear them down on shutdown.
        """
        cls._task_registry.clear()
        logger.info("CeleryStreamTask registry cleared")

    def __repr__(self) -> str:
        return f"CeleryStreamTask(id={self._id}, done={self.done})"
