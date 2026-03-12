import asyncio
import uuid
import logging
from typing import Optional, Dict, Callable, Awaitable

from app.domain.external.task import Task, TaskRunner, TaskBackend
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Runner factory — module-level so both API and worker processes can access
# ---------------------------------------------------------------------------

TaskRunnerFactory = Callable[[dict], Awaitable[TaskRunner]]

_runner_factory: Optional[TaskRunnerFactory] = None


def set_runner_factory(factory: TaskRunnerFactory) -> None:
    """Register the factory that Celery workers use to reconstruct a
    ``TaskRunner`` from serialisable context."""
    global _runner_factory
    _runner_factory = factory


def get_runner_factory() -> Optional[TaskRunnerFactory]:
    return _runner_factory


# ---------------------------------------------------------------------------
# Worker-side proxy
# ---------------------------------------------------------------------------

class _CeleryTaskProxy:
    """Minimal Task-like object used inside the Celery worker.

    Only exposes *input_stream* / *output_stream* — the subset that
    ``TaskRunner.run()`` actually needs.
    """

    def __init__(self, task_id: str):
        self._id = task_id
        self._input_stream = RedisStreamQueue(f"task:input:{task_id}")
        self._output_stream = RedisStreamQueue(f"task:output:{task_id}")

    @property
    def id(self) -> str:
        return self._id

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream


# ---------------------------------------------------------------------------
# Worker-side execution
# ---------------------------------------------------------------------------

async def _execute_in_worker(task_id: str, context: dict) -> None:
    """Run inside a Celery worker process.

    Uses the registered :func:`get_runner_factory` to build a
    ``TaskRunner`` from *context*, then executes it against a
    :class:`_CeleryTaskProxy`.
    """
    from app.domain.models.event import ErrorEvent

    task_proxy = _CeleryTaskProxy(task_id)

    factory = get_runner_factory()
    if factory is None:
        logger.error("Runner factory not configured for Celery worker")
        await task_proxy.output_stream.put(
            ErrorEvent(error="Runner factory not configured").model_dump_json()
        )
        return

    try:
        runner = await factory(context)
    except Exception as e:
        logger.exception("Failed to create TaskRunner for task %s", task_id)
        await task_proxy.output_stream.put(
            ErrorEvent(error=f"Runner creation failed: {e}").model_dump_json()
        )
        return

    try:
        await runner.run(task_proxy)
    except asyncio.CancelledError:
        logger.info("Celery task %s cancelled", task_id)
    except Exception as e:
        logger.exception("Celery task %s execution failed", task_id)
        await task_proxy.output_stream.put(
            ErrorEvent(error=f"Task error: {e}").model_dump_json()
        )
    finally:
        await runner.on_done(task_proxy)


def _register_celery_tasks() -> None:
    from app.infrastructure.external.task.celery_app import get_celery_app

    app = get_celery_app()

    @app.task(name="manus.execute_agent_task", bind=True)
    def execute_agent_task(self, task_id: str, context: dict):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_execute_in_worker(task_id, context))
        finally:
            loop.close()


_celery_tasks_registered = False


def _ensure_celery_tasks_registered() -> None:
    global _celery_tasks_registered
    if not _celery_tasks_registered:
        _register_celery_tasks()
        _celery_tasks_registered = True


# ---------------------------------------------------------------------------
# CeleryTask — API-side Task implementation
# ---------------------------------------------------------------------------

class CeleryTask(Task):
    """Task dispatched to a Celery worker.

    Communication with the worker still uses Redis Streams, so the API
    process can read events in real time.
    """

    def __init__(self, task_id: str, context: dict):
        self._id = task_id
        self._context = context
        self._celery_result = None

        self._input_stream = RedisStreamQueue(f"task:input:{task_id}")
        self._output_stream = RedisStreamQueue(f"task:output:{task_id}")

    @property
    def id(self) -> str:
        return self._id

    @property
    def done(self) -> bool:
        if self._celery_result is None:
            return True
        return self._celery_result.ready()

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream

    async def run(self) -> None:
        if not self.done:
            return

        _ensure_celery_tasks_registered()
        from app.infrastructure.external.task.celery_app import get_celery_app

        app = get_celery_app()
        self._celery_result = app.send_task(
            "manus.execute_agent_task",
            args=[self._id, self._context],
        )
        logger.info("Task %s dispatched to Celery worker", self._id)

    def cancel(self) -> bool:
        if self._celery_result and not self.done:
            self._celery_result.revoke(terminate=True)
            logger.info("Task %s revoked", self._id)
            return True
        return False

    def __repr__(self) -> str:
        return f"CeleryTask(id={self._id}, done={self.done})"


# ---------------------------------------------------------------------------
# CeleryTaskBackend
# ---------------------------------------------------------------------------

class CeleryTaskBackend(TaskBackend):
    """Celery-based :class:`TaskBackend`.

    Requires a *runner_factory* that can reconstruct a ``TaskRunner``
    from the serialisable context dict.  The factory is also registered
    at the module level so that Celery workers (separate processes)
    can access it.
    """

    def __init__(self, runner_factory: TaskRunnerFactory):
        self._tasks: Dict[str, CeleryTask] = {}
        self._runners: Dict[str, TaskRunner] = {}
        set_runner_factory(runner_factory)

    async def submit(self, runner: TaskRunner) -> Task:
        context = runner.get_context()
        task_id = str(uuid.uuid4())
        task = CeleryTask(task_id, context)
        self._tasks[task_id] = task
        self._runners[task_id] = runner
        logger.info("Task %s registered (celery)", task_id)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def shutdown(self) -> None:
        for task_id, task in list(self._tasks.items()):
            task.cancel()
            runner = self._runners.get(task_id)
            if runner:
                await runner.destroy()
        self._tasks.clear()
        self._runners.clear()
        logger.info("CeleryTaskBackend shutdown complete")
