from typing import Protocol, Any, Awaitable, Optional, Callable
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

    def get_context(self) -> dict:
        """Return serializable context for distributed task reconstruction.
        
        Override this in subclasses to provide the parameters a remote
        worker needs to recreate an equivalent TaskRunner instance.
        The default implementation returns an empty dict.
        """
        return {}

    @abstractmethod
    async def on_done(self, task: "Task") -> None:
        """Called when task execution is done.
        
        Use this method to handle graceful shutdown and cleanup.
        This method should ensure all resources are properly released.
        """
        ...

class Task(Protocol):
    """Protocol defining the interface for task management operations."""
    
    async def run(self) -> None:
        """Run a task."""
        ...
    
    def cancel(self) -> bool:
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
    
    @property
    def done(self) -> bool:
        """Check if the task is done.

        Returns:
            bool: True if the task is done, False otherwise
        """
        ...
    
    @classmethod
    def get(cls, task_id: str) -> Optional["Task"]:
        """Get a task by its ID.

        Returns:
            Optional[Task]: Task instance if found, None otherwise
        """
        ...
    
    @classmethod
    def create(cls, runner: TaskRunner) -> "Task":
        """Create a new task instance with the specified task runner.

        Args:
            runner (TaskRunner): The task runner that will execute this task

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
