import asyncio
import uuid
import logging
from typing import Any, Dict, Optional

from app.domain.external.task import Task, TaskRunner, TaskRunnerFactory
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue, MessageQueue

logger = logging.getLogger(__name__)


class RedisStreamTask(Task):
    """In-process task implementation backed by Redis Streams for I/O.

    The task runs as an asyncio task inside the current process; only the
    input/output streams live in Redis. The task registry is process-local.
    """
    
    _task_registry: Dict[str, 'RedisStreamTask'] = {}
    _runner_factory: Optional[TaskRunnerFactory] = None
    
    def __init__(self, params: Dict[str, Any]):
        """Initialize Redis Stream task with serializable runner parameters.
        
        Args:
            params: JSON-serializable parameters used by the registered
                TaskRunnerFactory to rebuild the runner when the task runs
        """
        self._params = params
        self._runner: Optional[TaskRunner] = None
        self._id = str(uuid.uuid4())
        self._execution_task: Optional[asyncio.Task] = None
        
        # Create input/output streams based on task ID
        input_stream_name = f"task:input:{self._id}"
        output_stream_name = f"task:output:{self._id}"
        self._input_stream = RedisStreamQueue(input_stream_name)
        self._output_stream = RedisStreamQueue(output_stream_name)
        
        # Register task instance
        RedisStreamTask._task_registry[self._id] = self
        
    @property
    def id(self) -> str:
        """Task ID."""
        return self._id
    
    @property
    def _done(self) -> bool:
        if self._execution_task is None:
            return True
        return self._execution_task.done()
    
    async def is_done(self) -> bool:
        """Check if the task is done.

        Returns:
            bool: True if the task is done, False otherwise
        """
        return self._done
    
    async def run(self) -> None:
        """Run the task using the runner built by the registered factory."""
        if self._done:
            if self._runner is None:
                if RedisStreamTask._runner_factory is None:
                    raise RuntimeError("No TaskRunnerFactory registered for RedisStreamTask")
                self._runner = await RedisStreamTask._runner_factory.create_runner(self._params)
            self._execution_task = asyncio.create_task(self._execute_task())
            logger.info(f"Task {self._id} execution started")
    
    async def cancel(self) -> bool:
        """Cancel the task.

        Returns:
            bool: True if the task is cancelled, False otherwise
        """
        if not self._done:
            self._execution_task.cancel()
            logger.info(f"Task {self._id} cancelled")
            self._cleanup_registry()
            return True
        
        self._cleanup_registry()
        return False
    
    @property
    def input_stream(self) -> MessageQueue:
        """Input stream."""
        return self._input_stream
    
    @property
    def output_stream(self) -> MessageQueue:
        """Output stream."""
        return self._output_stream
    
    def _on_task_done(self) -> None:
        """Called when the task is done."""
        if self._runner:
            asyncio.create_task(self._runner.on_done(self))
        self._cleanup_registry()
    
    def _cleanup_registry(self) -> None:
        """Remove this task from the registry."""
        if self._id in RedisStreamTask._task_registry:
            del RedisStreamTask._task_registry[self._id]
            logger.info(f"Task {self._id} removed from registry")
    
    async def _execute_task(self):
        """Execute the task using the TaskRunner."""
        try:
            await self._runner.run(self)
        except asyncio.CancelledError:
            logger.info(f"Task {self._id} execution cancelled")
        except Exception as e:
            logger.error(f"Task {self._id} execution failed: {str(e)}")
        finally:
            self._on_task_done()
    
    @classmethod
    def set_runner_factory(cls, factory: TaskRunnerFactory) -> None:
        """Register the factory used to rebuild task runners."""
        cls._runner_factory = factory
    
    @classmethod
    async def get(cls, task_id: str) -> Optional['RedisStreamTask']:
        """Get a task by its ID.

        Returns:
            Optional[RedisStreamTask]: Task instance if found, None otherwise
        """
        return cls._task_registry.get(task_id)
    
    @classmethod
    def create(cls, params: Dict[str, Any]) -> "RedisStreamTask":
        """Create a new task instance from serializable runner parameters.

        Args:
            params: JSON-serializable runner parameters

        Returns:
            RedisStreamTask: New task instance
        """
        return cls(params)

    @classmethod
    async def destroy(cls) -> None:
        """Destroy all task instances."""
        # Iterate over a copy: cancel() mutates the registry
        for task in list(cls._task_registry.values()):
            await task.cancel()
            if task._runner:
                await task._runner.destroy()
        cls._task_registry.clear()
    
    def __repr__(self) -> str:
        """String representation of the task."""
        return f"RedisStreamTask(id={self._id}, done={self._done})"
