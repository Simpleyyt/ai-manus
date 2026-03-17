import asyncio
import uuid
import logging
from typing import Any, Optional, Dict

from celery import Task as CeleryBaseTask
from celery.result import AsyncResult

from app.core.reflection import import_string
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
# Default worker initialiser — bootstraps MongoDB / Beanie / Redis.
# Pulled out as a standalone coroutine so it can be swapped via the
# component registry without touching AgentExecutionTask itself.
# ---------------------------------------------------------------------------

async def _default_worker_init() -> None:
    from app.core.config import get_settings

    mongodb = import_string("app.infrastructure.storage.mongodb.get_mongodb")()
    redis = import_string("app.infrastructure.storage.redis.get_redis")()
    init_beanie = import_string("beanie.init_beanie")
    documents = [
        import_string(path)
        for path in (
            "app.infrastructure.models.documents.AgentDocument",
            "app.infrastructure.models.documents.SessionDocument",
            "app.infrastructure.models.documents.UserDocument",
        )
    ]

    settings = get_settings()
    await mongodb.initialize()
    await init_beanie(
        database=mongodb.client[settings.mongodb_database],
        document_models=documents,
    )
    await redis.initialize()


# ---------------------------------------------------------------------------
# Worker-side: OOP-style Celery Task with lazy-loaded shared resources.
# All concrete classes are referenced as dotted-path strings in
# COMPONENT_REGISTRY and resolved at runtime via import_string(),
# so this module has zero direct imports of infrastructure implementations.
# ---------------------------------------------------------------------------

class AgentExecutionTask(CeleryBaseTask):
    """Celery OOP Task responsible for executing agent workflows in a worker.

    Every component the worker needs is declared as a dotted-path string in
    ``COMPONENT_REGISTRY``.  Override the registry (e.g. in a subclass or via
    configuration) to swap any implementation without touching this file.
    """

    name = "manus.agent.execute"
    ignore_result = False
    track_started = True
    max_retries = 0

    COMPONENT_REGISTRY: Dict[str, str] = {
        "worker_initializer": "app.infrastructure.external.task.celery_task._default_worker_init",
        "sandbox_cls": "app.infrastructure.external.sandbox.docker_sandbox.DockerSandbox",
        "task_runner_cls": "app.domain.services.agent_task_runner.AgentTaskRunner",
        "agent_repository": "app.infrastructure.repositories.mongo_agent_repository.MongoAgentRepository",
        "session_repository": "app.infrastructure.repositories.mongo_session_repository.MongoSessionRepository",
        "file_storage": "app.infrastructure.external.file.gridfsfile.get_file_storage",
        "search_engine": "app.infrastructure.external.search.get_search_engine",
        "mcp_repository": "app.infrastructure.repositories.file_mcp_repository.FileMCPRepository",
    }

    # ---- per-worker-process caches (class-level) ----
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _initialized: bool = False
    _resolved_classes: Dict[str, Any] = {}
    _singletons: Dict[str, Any] = {}

    # -- reflection helpers --------------------------------------------------

    def _resolve(self, key: str) -> Any:
        """Resolve a class / callable from the registry (cached per worker)."""
        if key not in self.__class__._resolved_classes:
            self.__class__._resolved_classes[key] = import_string(
                self.COMPONENT_REGISTRY[key]
            )
        return self.__class__._resolved_classes[key]

    def _singleton(self, key: str) -> Any:
        """Resolve, instantiate, and cache a component (once per worker)."""
        if key not in self.__class__._singletons:
            factory = self._resolve(key)
            self.__class__._singletons[key] = factory()
        return self.__class__._singletons[key]

    # -- event loop ----------------------------------------------------------

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self.__class__._loop is None or self.__class__._loop.is_closed():
            self.__class__._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.__class__._loop)
        return self.__class__._loop

    # -- async infrastructure bootstrap (once per worker) --------------------

    async def _ensure_initialized(self) -> None:
        if self.__class__._initialized:
            return
        initializer = self._resolve("worker_initializer")
        await initializer()
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

        sandbox_cls = self._resolve("sandbox_cls")
        task_runner_cls = self._resolve("task_runner_cls")

        sandbox = await sandbox_cls.get(sandbox_id)
        if not sandbox:
            raise RuntimeError(f"Sandbox {sandbox_id} not found")

        browser = await sandbox.get_browser()
        if not browser:
            raise RuntimeError(f"Failed to get browser for sandbox {sandbox_id}")

        runner = task_runner_cls(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            sandbox=sandbox,
            browser=browser,
            agent_repository=self._singleton("agent_repository"),
            session_repository=self._singleton("session_repository"),
            file_storage=self._singleton("file_storage"),
            search_engine=self._singleton("search_engine"),
            mcp_repository=self._singleton("mcp_repository"),
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

    META_ATTRIBUTES: Dict[str, str] = {
        "session_id": "_session_id",
        "agent_id": "_agent_id",
        "user_id": "_user_id",
    }
    SANDBOX_ATTR: str = "_sandbox"

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

    @classmethod
    def _extract_runner_meta(cls, runner: TaskRunner) -> dict:
        """Extract serialisable metadata from the runner via reflection."""
        meta = {
            key: getattr(runner, attr, None)
            for key, attr in cls.META_ATTRIBUTES.items()
        }
        sandbox = getattr(runner, cls.SANDBOX_ATTR, None)
        meta["sandbox_id"] = getattr(sandbox, "id", None) if sandbox else None
        return meta

    def __repr__(self) -> str:
        celery_id = self._celery_result.id if self._celery_result else None
        return (
            f"CeleryStreamTask(id={self._id}, "
            f"celery_id={celery_id}, done={self.done})"
        )
