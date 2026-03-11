import asyncio
import uuid
import logging
from typing import Optional, Dict

from app.domain.external.task import Task, TaskRunner
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue

logger = logging.getLogger(__name__)


class _CeleryTaskProxy:
    """Lightweight proxy used inside the Celery worker to provide the Task
    interface that ``AgentTaskRunner.run()`` expects (input_stream /
    output_stream).  The proxy reconstructs Redis Stream queues from the
    task ID so the worker can read/write the same streams as the API
    process."""

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
# Celery worker-side helpers
# ---------------------------------------------------------------------------

_worker_infrastructure_ready = False


async def _ensure_worker_infrastructure() -> None:
    """Initialise MongoDB / Beanie / Redis the first time a Celery worker
    executes a task.  Subsequent calls are no-ops."""
    global _worker_infrastructure_ready
    if _worker_infrastructure_ready:
        return

    from app.core.config import get_settings
    from app.infrastructure.storage.mongodb import get_mongodb
    from app.infrastructure.storage.redis import get_redis
    from app.infrastructure.models.documents import (
        AgentDocument,
        SessionDocument,
        UserDocument,
    )
    from beanie import init_beanie

    settings = get_settings()
    await get_mongodb().initialize()
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument],
    )
    await get_redis().initialize()
    _worker_infrastructure_ready = True
    logger.info("Celery worker infrastructure initialised")


async def _execute_in_worker(
    task_id: str,
    session_id: str,
    agent_id: str,
    user_id: str,
    sandbox_id: str,
) -> None:
    """Reconstruct dependencies and run the ``AgentTaskRunner`` inside the
    Celery worker process."""
    from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
    from app.infrastructure.external.file.gridfsfile import get_file_storage
    from app.infrastructure.external.search import get_search_engine
    from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
    from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
    from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
    from app.domain.services.agent_task_runner import AgentTaskRunner
    from app.domain.models.event import ErrorEvent

    await _ensure_worker_infrastructure()

    task_proxy = _CeleryTaskProxy(task_id)

    sandbox = await DockerSandbox.get(sandbox_id)
    if not sandbox:
        logger.error("Sandbox %s not found for task %s", sandbox_id, task_id)
        await task_proxy.output_stream.put(
            ErrorEvent(error=f"Sandbox {sandbox_id} not found").model_dump_json()
        )
        return

    browser = await sandbox.get_browser()
    if not browser:
        logger.error("Browser unavailable for sandbox %s", sandbox_id)
        await task_proxy.output_stream.put(
            ErrorEvent(error="Browser unavailable").model_dump_json()
        )
        return

    runner = AgentTaskRunner(
        session_id=session_id,
        agent_id=agent_id,
        user_id=user_id,
        sandbox=sandbox,
        browser=browser,
        agent_repository=MongoAgentRepository(),
        session_repository=MongoSessionRepository(),
        file_storage=get_file_storage(),
        mcp_repository=FileMCPRepository(),
        search_engine=get_search_engine(),
    )

    try:
        await runner.run(task_proxy)
    except asyncio.CancelledError:
        logger.info("Celery task %s cancelled", task_id)
    except Exception as e:
        logger.exception("Celery task %s execution failed", task_id)
        await task_proxy.output_stream.put(
            ErrorEvent(error=f"Task error: {e}").model_dump_json()
        )
    finally:
        await runner.on_done(task_proxy)


def _register_celery_tasks() -> None:
    """Register the Celery task function with the Celery app.

    Called lazily so that the Celery app is only created when actually
    needed (i.e. when ``task_backend=celery``).
    """
    from app.infrastructure.external.task.celery_app import get_celery_app

    app = get_celery_app()

    @app.task(name="manus.execute_agent_task", bind=True)
    def execute_agent_task(self, task_id: str, session_id: str,
                           agent_id: str, user_id: str, sandbox_id: str):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _execute_in_worker(task_id, session_id, agent_id, user_id, sandbox_id)
            )
        finally:
            loop.close()


_celery_tasks_registered = False


def _ensure_celery_tasks_registered() -> None:
    global _celery_tasks_registered
    if not _celery_tasks_registered:
        _register_celery_tasks()
        _celery_tasks_registered = True


# ---------------------------------------------------------------------------
# CeleryTask – API-side class implementing the Task protocol
# ---------------------------------------------------------------------------

class CeleryTask(Task):
    """Celery-based task implementation following the Task protocol.

    Execution is dispatched to a Celery worker.  Input / output
    communication still uses Redis Streams so the API process can
    read events produced by the worker in real time.
    """

    _task_registry: Dict[str, "CeleryTask"] = {}

    def __init__(self, runner: TaskRunner):
        self._runner = runner
        self._id = str(uuid.uuid4())
        self._celery_result = None

        self._input_stream = RedisStreamQueue(f"task:input:{self._id}")
        self._output_stream = RedisStreamQueue(f"task:output:{self._id}")

        # Extract serialisable context from the runner so the Celery worker
        # can reconstruct dependencies independently.
        self._session_id: str = getattr(runner, "_session_id", "")
        self._agent_id: str = getattr(runner, "_agent_id", "")
        self._user_id: str = getattr(runner, "_user_id", "")
        sandbox = getattr(runner, "_sandbox", None)
        self._sandbox_id: str = sandbox.id if sandbox else ""

        CeleryTask._task_registry[self._id] = self

    # -- Task protocol properties -------------------------------------------

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

    # -- Task protocol methods ----------------------------------------------

    async def run(self) -> None:
        """Dispatch execution to a Celery worker."""
        if not self.done:
            return

        _ensure_celery_tasks_registered()
        from app.infrastructure.external.task.celery_app import get_celery_app

        app = get_celery_app()
        self._celery_result = app.send_task(
            "manus.execute_agent_task",
            args=[
                self._id,
                self._session_id,
                self._agent_id,
                self._user_id,
                self._sandbox_id,
            ],
        )
        logger.info("Task %s dispatched to Celery worker", self._id)

    def cancel(self) -> bool:
        if self._celery_result and not self.done:
            self._celery_result.revoke(terminate=True)
            logger.info("Task %s revoked", self._id)
            self._cleanup_registry()
            return True

        self._cleanup_registry()
        return False

    # -- Class methods (Task protocol) --------------------------------------

    @classmethod
    def get(cls, task_id: str) -> Optional["CeleryTask"]:
        return cls._task_registry.get(task_id)

    @classmethod
    def create(cls, runner: TaskRunner) -> "CeleryTask":
        return cls(runner)

    @classmethod
    async def destroy(cls) -> None:
        for task in list(cls._task_registry.values()):
            task.cancel()
            if task._runner:
                await task._runner.destroy()
        cls._task_registry.clear()

    # -- Internal helpers ---------------------------------------------------

    def _cleanup_registry(self) -> None:
        if self._id in CeleryTask._task_registry:
            del CeleryTask._task_registry[self._id]
            logger.info("Task %s removed from registry", self._id)

    def __repr__(self) -> str:
        return f"CeleryTask(id={self._id}, done={self.done})"
