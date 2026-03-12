from typing import Protocol, Optional
from abc import ABC, abstractmethod
from app.domain.external.message_queue import MessageQueue


class Task(Protocol):
    """Execution container with communication channels.

    A Task is a lightweight handle representing a running (or completed)
    unit of work.  It exposes input/output message streams for
    communication and basic lifecycle controls (run / cancel / done).

    Task instances are created and managed by a :class:`TaskBackend`.
    """

    @property
    def id(self) -> str:
        """Unique task identifier."""
        ...

    @property
    def done(self) -> bool:
        """Whether the task has finished."""
        ...

    @property
    def input_stream(self) -> MessageQueue:
        """Stream for sending messages *into* the task."""
        ...

    @property
    def output_stream(self) -> MessageQueue:
        """Stream for reading messages *from* the task."""
        ...

    async def run(self) -> None:
        """Start or resume task execution."""
        ...

    def cancel(self) -> bool:
        """Cancel a running task.

        Returns ``True`` if the task was actually cancelled.
        """
        ...


class TaskRunner(ABC):
    """Business logic executed inside a :class:`Task`.

    Implementations contain the core processing loop (reading from the
    task's input stream, writing to its output stream, etc.).
    """

    @abstractmethod
    async def run(self, task: Task) -> None:
        """Main execution logic."""
        ...

    @abstractmethod
    async def destroy(self) -> None:
        """Release all resources held by this runner."""
        ...

    @abstractmethod
    async def on_done(self, task: Task) -> None:
        """Called when the task finishes (success, failure, or cancellation)."""
        ...



class TaskBackend(ABC):
    """Manages the full lifecycle of tasks: creation, lookup, and shutdown.

    Different backends (in-process asyncio, Celery, …) provide their
    own implementations while the domain layer only depends on this
    interface.
    """

    @abstractmethod
    async def submit(self, runner: TaskRunner) -> Task:
        """Create a new :class:`Task` backed by *runner* and register it.

        The task is **not** started automatically — the caller should
        invoke ``task.run()`` when ready.
        """
        ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a previously submitted task, or ``None``."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cancel all running tasks and release resources."""
        ...
