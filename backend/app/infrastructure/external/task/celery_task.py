import uuid
import logging
from typing import Optional, Dict

from app.domain.external.task import Task, TaskRunner, TaskBackend
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level runner registry — shared between the API process and an
# embedded (same-process) Celery worker so the runner created by the
# domain service can be executed without reconstruction.
# ---------------------------------------------------------------------------

_runner_registry: Dict[str, TaskRunner] = {}


def get_runner(task_id: str) -> Optional[TaskRunner]:
    """Retrieve a runner stored during :meth:`CeleryTaskBackend.submit`."""
    return _runner_registry.get(task_id)


def remove_runner(task_id: str) -> None:
    """Remove a runner after execution completes."""
    _runner_registry.pop(task_id, None)


# ---------------------------------------------------------------------------
# CeleryTaskProxy — lightweight proxy used inside the Celery worker
# ---------------------------------------------------------------------------

class CeleryTaskProxy:
    """Minimal Task-like object for the Celery worker.

    Exposes *id*, *input_stream* and *output_stream* — the subset that
    ``TaskRunner.run()`` needs.
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
# CeleryTask — API-side handle
# ---------------------------------------------------------------------------

class CeleryTask(Task):
    """Task whose execution is dispatched to a Celery worker."""

    def __init__(self, task_id: str):
        self._id = task_id
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
        from app.infrastructure.external.task.celery_app import get_celery_app

        app = get_celery_app()
        self._celery_result = app.send_task(
            "manus.execute_agent_task",
            args=[self._id],
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

    Stores runners in a module-level registry so that an embedded
    (same-process) Celery worker can look them up directly — no
    serialisation or factory reconstruction needed.
    """

    def __init__(self):
        self._tasks: Dict[str, CeleryTask] = {}

    async def submit(self, runner: TaskRunner) -> Task:
        task_id = str(uuid.uuid4())
        _runner_registry[task_id] = runner
        task = CeleryTask(task_id)
        self._tasks[task_id] = task
        logger.info("Task %s registered (celery)", task_id)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def shutdown(self) -> None:
        for task_id, task in list(self._tasks.items()):
            task.cancel()
            runner = _runner_registry.pop(task_id, None)
            if runner:
                await runner.destroy()
        self._tasks.clear()
        logger.info("CeleryTaskBackend shutdown complete")
