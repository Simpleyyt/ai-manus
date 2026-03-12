from __future__ import annotations

from typing import Optional, Callable, Awaitable
from abc import ABC, abstractmethod
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue
import uuid


class TaskExecutor(ABC):
    """Strategy that controls *how* a Task runs (asyncio / Celery / …)."""

    @abstractmethod
    async def start(self, task: Task) -> None: ...

    @abstractmethod
    def is_done(self) -> bool: ...

    @abstractmethod
    def cancel(self) -> bool: ...


class Task(ABC):
    """Base task — like Java's ``Thread``.

    Subclass and override :meth:`run`.  Call :meth:`start` to begin
    execution in whatever backend is configured.

    * ``run()``   — business logic, executed in the task's process/thread
    * ``start()`` — dispatches execution (set by the backend via ``_executor``)
    * ``done``    — whether execution has finished
    * ``cancel()``— request cancellation
    """

    def __init__(self, session_id: str, task_id: str | None = None):
        self._id = task_id or str(uuid.uuid4())
        self._session_id = session_id
        self._executor: TaskExecutor | None = None
        self._input_stream = RedisStreamQueue(f"task:input:{self._id}")
        self._output_stream = RedisStreamQueue(f"task:output:{self._id}")

    # -- abstract: subclass must implement ----------------------------------

    @abstractmethod
    async def run(self) -> None:
        """Business logic. Runs in the task's execution context."""
        ...

    async def destroy(self) -> None:
        """Release resources (sandbox, MCP, …)."""

    async def on_complete(self) -> None:
        """Called after ``run()`` finishes (success or failure)."""

    # -- lifecycle (delegated to executor) ----------------------------------

    async def start(self) -> None:
        if self._executor:
            await self._executor.start(self)

    @property
    def done(self) -> bool:
        return self._executor.is_done() if self._executor else True

    def cancel(self) -> bool:
        return self._executor.cancel() if self._executor else False

    # -- properties ---------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream


class TaskBackend(ABC):
    """Creates and manages tasks."""

    def set_task_creator(self, fn: Callable[[str, str | None], Awaitable[Task]]) -> None:
        """Inject ``async (session_id, task_id?) -> Task`` after construction."""

    @abstractmethod
    async def submit(self, session_id: str) -> Task: ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]: ...

    @abstractmethod
    async def shutdown(self) -> None: ...
