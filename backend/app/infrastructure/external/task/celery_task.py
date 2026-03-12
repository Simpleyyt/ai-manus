import asyncio
import uuid
import logging
from typing import Optional, Dict

from celery import Task as CeleryBaseTask
from celery.result import AsyncResult

from app.domain.external.task import Task, TaskRunner
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.external.message_queue.redis_stream_queue import RedisStreamQueue
from app.infrastructure.external.task.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Worker-side: lightweight Task proxy used inside the Celery worker process.
# It only exposes the stream interfaces that AgentTaskRunner actually needs.
# ---------------------------------------------------------------------------

class _WorkerTaskProxy:
    """Minimal Task-compatible proxy for Celery worker execution context."""

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

    @property
    def done(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Worker-side: OOP-style Celery Task with lazy-loaded shared resources.
# Resources are initialized once per worker process and reused across
# subsequent task invocations, following the pattern recommended by Celery.
# ---------------------------------------------------------------------------

class AgentExecutionTask(CeleryBaseTask):
    """Celery OOP Task responsible for executing agent workflows in a worker.

    Shared infrastructure (DB connections, repositories, storage) is lazily
    initialised on first use and then reused for every subsequent task that
    lands on the same worker process.
    """

    name = "manus.agent.execute"
    ignore_result = False
    track_started = True
    max_retries = 0

    # ---- per-worker-process state (class-level, shared across invocations) ----
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _initialized: bool = False
    _agent_repo = None
    _session_repo = None
    _file_storage = None
    _search_engine = None
    _mcp_repository = None

    # -- event loop ----------------------------------------------------------

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self.__class__._loop is None or self.__class__._loop.is_closed():
            self.__class__._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.__class__._loop)
        return self.__class__._loop

    # -- lazy resource properties --------------------------------------------

    @property
    def agent_repository(self):
        if self.__class__._agent_repo is None:
            from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
            self.__class__._agent_repo = MongoAgentRepository()
        return self.__class__._agent_repo

    @property
    def session_repository(self):
        if self.__class__._session_repo is None:
            from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
            self.__class__._session_repo = MongoSessionRepository()
        return self.__class__._session_repo

    @property
    def file_storage(self):
        if self.__class__._file_storage is None:
            from app.infrastructure.external.file.gridfsfile import get_file_storage
            self.__class__._file_storage = get_file_storage()
        return self.__class__._file_storage

    @property
    def search_engine(self):
        if self.__class__._search_engine is None:
            from app.infrastructure.external.search import get_search_engine
            self.__class__._search_engine = get_search_engine()
        return self.__class__._search_engine

    @property
    def mcp_repository(self):
        if self.__class__._mcp_repository is None:
            from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
            self.__class__._mcp_repository = FileMCPRepository()
        return self.__class__._mcp_repository

    # -- async infrastructure bootstrap (once per worker) --------------------

    async def _ensure_initialized(self) -> None:
        if self.__class__._initialized:
            return

        from app.infrastructure.storage.mongodb import get_mongodb
        from app.infrastructure.storage.redis import get_redis
        from app.infrastructure.models.documents import (
            AgentDocument, SessionDocument, UserDocument,
        )
        from beanie import init_beanie
        from app.core.config import get_settings

        settings = get_settings()

        await get_mongodb().initialize()
        await init_beanie(
            database=get_mongodb().client[settings.mongodb_database],
            document_models=[AgentDocument, SessionDocument, UserDocument],
        )
        await get_redis().initialize()

        self.__class__._initialized = True
        logger.info("Celery worker infrastructure initialized")

    # -- Celery entry point --------------------------------------------------

    def run(
        self,
        task_id: str,
        session_id: str,
        agent_id: str,
        user_id: str,
        sandbox_id: str,
    ) -> dict:
        """Synchronous Celery entry point — bridges into async execution."""
        try:
            return self.loop.run_until_complete(
                self._async_run(task_id, session_id, agent_id, user_id, sandbox_id)
            )
        except Exception as e:
            logger.exception(f"Task {task_id} execution failed")
            return {"status": "error", "task_id": task_id, "message": str(e)}

    async def _async_run(
        self,
        task_id: str,
        session_id: str,
        agent_id: str,
        user_id: str,
        sandbox_id: str,
    ) -> dict:
        await self._ensure_initialized()

        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        from app.domain.services.agent_task_runner import AgentTaskRunner

        sandbox = await DockerSandbox.get(sandbox_id)
        if not sandbox:
            raise RuntimeError(f"Sandbox {sandbox_id} not found")

        browser = await sandbox.get_browser()
        if not browser:
            raise RuntimeError(f"Failed to get browser for sandbox {sandbox_id}")

        runner = AgentTaskRunner(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            sandbox=sandbox,
            browser=browser,
            agent_repository=self.agent_repository,
            session_repository=self.session_repository,
            file_storage=self.file_storage,
            search_engine=self.search_engine,
            mcp_repository=self.mcp_repository,
        )

        proxy = _WorkerTaskProxy(task_id)

        try:
            await runner.run(proxy)
            return {"status": "completed", "task_id": task_id}
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} cancelled in worker")
            return {"status": "cancelled", "task_id": task_id}
        except Exception as e:
            logger.exception(f"Task {task_id} runner failed")
            return {"status": "error", "task_id": task_id, "message": str(e)}
        finally:
            await runner.on_done(proxy)


celery_app.register_task(AgentExecutionTask())


# ---------------------------------------------------------------------------
# API-side: CeleryStreamTask implements the domain Task protocol and
# dispatches execution to a Celery worker via AgentExecutionTask.
# ---------------------------------------------------------------------------

class CeleryStreamTask(Task):
    """Celery-backed implementation of the domain Task protocol.

    The API server creates instances of this class.  When ``run()`` is called
    the heavy lifting is dispatched to a Celery worker through
    ``AgentExecutionTask``, while real-time event streaming still flows
    through Redis Streams (same as RedisStreamTask).
    """

    _task_registry: Dict[str, "CeleryStreamTask"] = {}

    def __init__(self, runner: TaskRunner):
        self._runner = runner
        self._id = str(uuid.uuid4())
        self._celery_result: Optional[AsyncResult] = None

        self._input_stream = RedisStreamQueue(f"task:input:{self._id}")
        self._output_stream = RedisStreamQueue(f"task:output:{self._id}")

        self._runner_meta = self._extract_runner_meta(runner)

        CeleryStreamTask._task_registry[self._id] = self

    # -- Task protocol -------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def done(self) -> bool:
        if self._celery_result is None:
            return True
        return self._celery_result.ready()

    async def run(self) -> None:
        if self.done:
            task_impl = celery_app.tasks[AgentExecutionTask.name]
            self._celery_result = task_impl.apply_async(
                kwargs={
                    "task_id": self._id,
                    **self._runner_meta,
                },
            )
            logger.info(
                f"Task {self._id} dispatched to Celery "
                f"(celery_id={self._celery_result.id})"
            )

    def cancel(self) -> bool:
        if self._celery_result and not self.done:
            self._celery_result.revoke(terminate=True)
            logger.info(f"Task {self._id} cancelled")
            self._cleanup_registry()
            return True
        self._cleanup_registry()
        return False

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream

    # -- class-level registry ------------------------------------------------

    @classmethod
    def get(cls, task_id: str) -> Optional["CeleryStreamTask"]:
        return cls._task_registry.get(task_id)

    @classmethod
    def create(cls, runner: TaskRunner) -> "CeleryStreamTask":
        return cls(runner)

    @classmethod
    async def destroy(cls) -> None:
        for task in list(cls._task_registry.values()):
            task.cancel()
            if task._runner:
                await task._runner.destroy()
        cls._task_registry.clear()

    # -- internals -----------------------------------------------------------

    def _cleanup_registry(self) -> None:
        if self._id in CeleryStreamTask._task_registry:
            del CeleryStreamTask._task_registry[self._id]
            logger.info(f"Task {self._id} removed from registry")

    @staticmethod
    def _extract_runner_meta(runner: TaskRunner) -> dict:
        """Extract serialisable metadata from the runner for Celery dispatch."""
        sandbox = getattr(runner, "_sandbox", None)
        return {
            "session_id": getattr(runner, "_session_id", None),
            "agent_id": getattr(runner, "_agent_id", None),
            "user_id": getattr(runner, "_user_id", None),
            "sandbox_id": getattr(sandbox, "id", None) if sandbox else None,
        }

    def __repr__(self) -> str:
        celery_id = self._celery_result.id if self._celery_result else None
        return (
            f"CeleryStreamTask(id={self._id}, "
            f"celery_id={celery_id}, done={self.done})"
        )
