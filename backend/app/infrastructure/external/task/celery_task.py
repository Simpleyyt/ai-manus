import logging
from typing import Optional, Dict

from app.domain.external.task import Task, TaskExecutor, TaskBackend
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue
import uuid

logger = logging.getLogger(__name__)


class CeleryExecutor(TaskExecutor):
    """Dispatches execution to a Celery worker."""

    def __init__(self):
        self._celery_result = None

    async def start(self, task: Task) -> None:
        if not self.is_done():
            return
        from app.infrastructure.external.task.celery_app import get_celery_app

        app = get_celery_app()
        self._celery_result = app.send_task(
            "manus.execute_agent_task",
            args=[task.id, task.session_id],
        )
        logger.info("Task %s dispatched to Celery worker", task.id)

    def is_done(self) -> bool:
        return self._celery_result is None or self._celery_result.ready()

    def cancel(self) -> bool:
        if self._celery_result and not self.is_done():
            self._celery_result.revoke(terminate=True)
            logger.info("Task revoked")
            return True
        return False


class CeleryTaskProxy:
    """Minimal Task-like object for the Celery worker.

    Exposes *id*, *input_stream* and *output_stream* — the subset that
    ``AgentTask.run()`` needs when executed in a remote worker.
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


class _RemoteTaskHandle(Task):
    """Lightweight API-side handle. ``run()`` is never called locally."""

    async def run(self) -> None:
        pass


class CeleryTaskBackend(TaskBackend):
    """Celery-based :class:`TaskBackend`.

    Dispatches ``session_id`` to a Celery worker.  The worker calls
    ``AgentService.create_task()`` to build the real :class:`AgentTask`
    and execute its ``run()`` — same code path as Redis, no duplication.
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    async def submit(self, session_id: str) -> Task:
        task_id = str(uuid.uuid4())
        handle = _RemoteTaskHandle(session_id, task_id)
        handle._executor = CeleryExecutor()
        self._tasks[task_id] = handle
        logger.info("Task %s registered (celery)", task_id)
        return handle

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        self._tasks.clear()
        logger.info("CeleryTaskBackend shutdown complete")
