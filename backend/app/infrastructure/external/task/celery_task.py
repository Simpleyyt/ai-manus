import asyncio
import uuid
import logging
from typing import Optional, Dict, Callable, Awaitable

from app.domain.external.task import Task, TaskRunner
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)

# Type alias for the runner factory callable.
# Accepts a context dict (from TaskRunner.get_context()) and returns a TaskRunner.
TaskRunnerFactory = Callable[[dict], Awaitable[TaskRunner]]


class _CeleryTaskProxy:
    """Lightweight proxy used inside the Celery worker to provide the Task
    interface that ``TaskRunner.run()`` expects (input_stream /
    output_stream).  The proxy reconstructs Redis Stream queues from the
    task ID so the worker can read/write the same streams as the API
    process."""

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
# Celery worker-side execution
# ---------------------------------------------------------------------------

async def _execute_in_worker(task_id: str, context: dict) -> None:
    """Execute a task inside the Celery worker.

    Uses the runner factory registered via
    ``CeleryTask.set_runner_factory()`` to construct the ``TaskRunner``
    from the serialisable *context*, keeping this module free of any
    concrete infrastructure dependency.
    """
    from app.domain.models.event import ErrorEvent

    task_proxy = _CeleryTaskProxy(task_id)

    factory = CeleryTask.get_runner_factory()
    if factory is None:
        logger.error("CeleryTask runner factory not configured")
        await task_proxy.output_stream.put(
            ErrorEvent(error="CeleryTask runner factory not configured").model_dump_json()
        )
        return

    try:
        runner = await factory(context)
    except Exception as e:
        logger.exception("Failed to create TaskRunner from context for task %s", task_id)
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
    """Register the Celery task function with the Celery app.

    Called lazily so that the Celery app is only created when actually
    needed (i.e. when ``task_backend=celery``).
    """
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
# CeleryTask – API-side class implementing the Task protocol
# ---------------------------------------------------------------------------

class CeleryTask(Task):
    """Celery-based task implementation following the Task protocol.

    Execution is dispatched to a Celery worker.  Input / output
    communication still uses Redis Streams so the API process can
    read events produced by the worker in real time.

    Before dispatching tasks, a ``TaskRunnerFactory`` must be registered
    via ``set_runner_factory()`` so the worker can reconstruct a
    ``TaskRunner`` without depending on concrete implementations.
    """

    _task_registry: Dict[str, "CeleryTask"] = {}
    _runner_factory: Optional[TaskRunnerFactory] = None

    def __init__(self, runner: TaskRunner):
        self._runner = runner
        self._id = str(uuid.uuid4())
        self._celery_result = None

        self._input_stream = RedisStreamQueue(f"task:input:{self._id}")
        self._output_stream = RedisStreamQueue(f"task:output:{self._id}")

        self._context: dict = runner.get_context()

        CeleryTask._task_registry[self._id] = self

    # -- Factory configuration ----------------------------------------------

    @classmethod
    def set_runner_factory(cls, factory: TaskRunnerFactory) -> None:
        """Register the factory used by Celery workers to create TaskRunners."""
        cls._runner_factory = factory

    @classmethod
    def get_runner_factory(cls) -> Optional[TaskRunnerFactory]:
        return cls._runner_factory

    # -- Task protocol properties -------------------------------------------

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

    # -- Task protocol methods ----------------------------------------------

    async def run(self) -> None:
        """Dispatch execution to a Celery worker."""
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
            self._cleanup_registry()
            return True

        self._cleanup_registry()
        return False

    # -- Class methods (Task protocol) --------------------------------------

    @classmethod
    def get(cls, task_id: str) -> Optional["CeleryTask"]:
        return cls._task_registry.get(task_id)

    @classmethod
    def create(cls, runner: TaskRunner) -> "CeleryTask":
        return cls(runner)

    @classmethod
    async def destroy(cls) -> None:
        for task in list(cls._task_registry.values()):
            task.cancel()
            if task._runner:
                await task._runner.destroy()
        cls._task_registry.clear()

    # -- Internal helpers ---------------------------------------------------

    def _cleanup_registry(self) -> None:
        if self._id in CeleryTask._task_registry:
            del CeleryTask._task_registry[self._id]
            logger.info("Task %s removed from registry", self._id)

    def __repr__(self) -> str:
        return f"CeleryTask(id={self._id}, done={self.done})"
