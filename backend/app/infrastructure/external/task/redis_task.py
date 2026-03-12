import asyncio
import uuid
import logging
from typing import Optional, Dict, Callable

from app.domain.external.task import Task, TaskRunner, TaskBackend
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)


class RedisStreamTask(Task):
    """In-process asyncio task backed by Redis Streams for I/O."""

    def __init__(
        self,
        task_id: str,
        runner: TaskRunner,
        on_complete: Optional[Callable[[str], None]] = None,
    ):
        self._id = task_id
        self._runner = runner
        self._execution_task: Optional[asyncio.Task] = None
        self._on_complete = on_complete

        self._input_stream = RedisStreamQueue(f"task:input:{task_id}")
        self._output_stream = RedisStreamQueue(f"task:output:{task_id}")

    @property
    def id(self) -> str:
        return self._id

    @property
    def done(self) -> bool:
        if self._execution_task is None:
            return True
        return self._execution_task.done()

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream

    async def run(self) -> None:
        if self.done:
            self._execution_task = asyncio.create_task(self._execute())
            logger.info("Task %s execution started", self._id)

    def cancel(self) -> bool:
        if not self.done:
            self._execution_task.cancel()
            logger.info("Task %s cancelled", self._id)
            self._notify_complete()
            return True
        self._notify_complete()
        return False

    # -- internal -----------------------------------------------------------

    async def _execute(self):
        try:
            await self._runner.run(self)
        except asyncio.CancelledError:
            logger.info("Task %s execution cancelled", self._id)
        except Exception as e:
            logger.error("Task %s execution failed: %s", self._id, e)
        finally:
            if self._runner:
                asyncio.create_task(self._runner.on_done(self))
            self._notify_complete()

    def _notify_complete(self) -> None:
        if self._on_complete:
            self._on_complete(self._id)

    def __repr__(self) -> str:
        return f"RedisStreamTask(id={self._id}, done={self.done})"


class RedisTaskBackend(TaskBackend):
    """In-process :class:`TaskBackend` using asyncio + Redis Streams."""

    def __init__(self):
        self._tasks: Dict[str, RedisStreamTask] = {}

    async def submit(self, runner: TaskRunner) -> Task:
        task_id = str(uuid.uuid4())
        task = RedisStreamTask(task_id, runner, on_complete=self._remove)
        self._tasks[task_id] = task
        logger.info("Task %s registered", task_id)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
            if task._runner:
                await task._runner.destroy()
        self._tasks.clear()
        logger.info("RedisTaskBackend shutdown complete")

    def _remove(self, task_id: str) -> None:
        if self._tasks.pop(task_id, None):
            logger.info("Task %s removed from registry", task_id)
