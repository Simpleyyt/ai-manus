import asyncio
import logging
from typing import Optional, Dict, Callable, Awaitable

from app.domain.external.task import Task, TaskExecutor, TaskBackend

logger = logging.getLogger(__name__)


class AsyncExecutor(TaskExecutor):
    """Runs ``Task.run()`` in-process via :func:`asyncio.create_task`."""

    def __init__(self, on_complete: Callable[[str], None] | None = None):
        self._asyncio_task: asyncio.Task | None = None
        self._on_complete = on_complete

    async def start(self, task: Task) -> None:
        if self.is_done():
            self._asyncio_task = asyncio.create_task(self._execute(task))
            logger.info("Task %s execution started", task.id)

    def is_done(self) -> bool:
        return self._asyncio_task is None or self._asyncio_task.done()

    def cancel(self) -> bool:
        if self._asyncio_task and not self._asyncio_task.done():
            self._asyncio_task.cancel()
            logger.info("Task %s cancelled", "?")
            return True
        return False

    async def _execute(self, task: Task) -> None:
        try:
            await task.run()
        except asyncio.CancelledError:
            logger.info("Task %s execution cancelled", task.id)
        except Exception as e:
            logger.error("Task %s execution failed: %s", task.id, e)
        finally:
            await task.on_complete()
            if self._on_complete:
                self._on_complete(task.id)


class RedisTaskBackend(TaskBackend):
    """In-process :class:`TaskBackend` using asyncio + Redis Streams."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._create_task: Callable[[str, str | None], Awaitable[Task]] | None = None

    def set_task_creator(self, fn: Callable[[str, str | None], Awaitable[Task]]) -> None:
        self._create_task = fn

    async def submit(self, session_id: str) -> Task:
        task = await self._create_task(session_id, None)
        task._executor = AsyncExecutor(on_complete=self._remove)
        self._tasks[task.id] = task
        logger.info("Task %s registered (redis)", task.id)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
            await task.destroy()
        self._tasks.clear()
        logger.info("RedisTaskBackend shutdown complete")

    def _remove(self, task_id: str) -> None:
        if self._tasks.pop(task_id, None):
            logger.info("Task %s removed from registry", task_id)
