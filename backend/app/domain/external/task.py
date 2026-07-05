from typing import Any, Dict, Optional, Protocol
from abc import ABC, abstractmethod
from app.domain.external.message_queue import MessageQueue


class TaskRunner(ABC):
    """Abstract base class defining the interface for task runners.
    
    This interface defines two essential lifecycle methods:
    - run: Main task execution logic
    - on_stop: Called when task execution needs to stop
    """

    @abstractmethod
    async def run(self, task: "Task") -> None:
        """Main task execution logic.
        
        This method contains the core functionality of the task.
        Implementations should handle setup, execution, and cleanup.
        """
        ...
    
    @abstractmethod
    async def destroy(self) -> None:
        """Destroy the task and release resources.
        
        Called when the task needs to be destroyed.
        This method is responsible for cleaning up and releasing all resources used by the task,
        including but not limited to:
        - Closing network connections
        - Freeing memory
        - Cleaning up temporary files
        - Stopping background processes etc.
        """
        ...

    @abstractmethod
    async def on_done(self, task: "Task") -> None:
        """Called when task execution is done.
        
        Use this method to handle graceful shutdown and cleanup.
        This method should ensure all resources are properly released.
        """
        ...


class TaskRunnerFactory(ABC):
    """Factory that rebuilds a TaskRunner from serializable parameters.

    Task backends receive only JSON-serializable parameters when a task is
    created, so that execution can happen in another process (e.g. a Celery
    worker). The factory is responsible for reconstructing the runner with
    all its live dependencies on the side that actually executes the task.
    """

    @abstractmethod
    async def create_runner(self, params: Dict[str, Any]) -> TaskRunner:
        """Create a task runner from serializable parameters."""
        ...


class Task(Protocol):
    """Protocol defining the interface for task management operations."""
    
    async def run(self) -> None:
        """Run a task."""
        ...
    
    async def cancel(self) -> bool:
        """Cancel a task.

        Returns:
            bool: True if the task is cancelled, False otherwise
        """
        ...
    
    @property
    def input_stream(self) -> MessageQueue:
        """Input stream."""
        ...
    
    @property
    def output_stream(self) -> MessageQueue:
        """Output stream."""
        ...
    
    @property
    def id(self) -> str:
        """Task ID."""
        ...
    
    async def is_done(self) -> bool:
        """Check if the task is done.

        Returns:
            bool: True if the task is done, False otherwise
        """
        ...
    
    @classmethod
    def set_runner_factory(cls, factory: TaskRunnerFactory) -> None:
        """Register the factory used to rebuild task runners on the execution side."""
        ...
    
    @classmethod
    async def get(cls, task_id: str) -> Optional["Task"]:
        """Get a task by its ID.

        Returns:
            Optional[Task]: Task instance if found, None otherwise
        """
        ...
    
    @classmethod
    def create(cls, params: Dict[str, Any]) -> "Task":
        """Create a new task instance from serializable runner parameters.

        Args:
            params (Dict[str, Any]): JSON-serializable parameters used by the
                registered TaskRunnerFactory to rebuild the runner where the
                task is executed.

        Returns:
            Task: New task instance
        """
        ...

    @classmethod
    async def destroy(cls) -> None:
        """Destroy all task instances.
        
        Cleans up all running tasks and releases associated resources.
        """
        ...
