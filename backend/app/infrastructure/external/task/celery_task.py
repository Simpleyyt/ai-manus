import uuid
import logging
from typing import Optional, Dict

from app.domain.external.task import Task, TaskRunner, TaskBackend
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)


class CeleryTaskProxy:
    """Minimal Task-like object used inside a Celery worker.

    Only exposes *id*, *input_stream* and *output_stream* — the subset
    that ``TaskRunner.run()`` actually needs.  Reconstructs Redis Stream
    queues from the task ID so the worker can share the same streams as
    the API process.
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
# CeleryTask — API-side Task implementation
# ---------------------------------------------------------------------------

class CeleryTask(Task):
    """Task dispatched to a Celery worker.

    Communication with the worker still happens via Redis Streams, so
    the API process can read events in real time.
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

    Dispatches work to a named Celery task.  What the worker does with
    the context is entirely the application layer's concern — this
    backend only handles dispatch, tracking and shutdown.
    """

    def __init__(self):
        self._tasks: Dict[str, CeleryTask] = {}
        self._runners: Dict[str, TaskRunner] = {}

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
