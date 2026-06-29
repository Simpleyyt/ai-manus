"""Factory for rebuilding an :class:`AgentTaskRunner` inside a Celery worker.

When the agent task runs in-process (``RedisStreamTask``) the runner object is
constructed in the API process and handed to the task directly. With Celery the
task executes in a separate worker process, so the runner — which holds
non-serializable dependencies (sandbox, browser, repositories, ...) — has to be
rebuilt there from the only thing we can ship across the wire: the session id.

This mirrors the construction done in
``AgentDomainService._create_task`` but resolves the sandbox/browser from the
already-provisioned ``session.sandbox_id`` instead of creating new ones.
"""

import logging
from typing import Optional

from app.domain.services.agent_task_runner import AgentTaskRunner
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.file.gridfsfile import get_file_storage
from app.infrastructure.external.search import get_search_engine
from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository

logger = logging.getLogger(__name__)


async def create_agent_task_runner(session_id: str) -> Optional[AgentTaskRunner]:
    """Rebuild the :class:`AgentTaskRunner` for ``session_id`` in a worker."""
    session_repository = MongoSessionRepository()
    session = await session_repository.find_by_id(session_id)
    if not session:
        logger.error(f"Cannot build runner: session {session_id} not found")
        return None

    sandbox = None
    if session.sandbox_id:
        sandbox = await DockerSandbox.get(session.sandbox_id)
    if not sandbox:
        sandbox = await DockerSandbox.create()
        session.sandbox_id = sandbox.id
        await session_repository.save(session)

    browser = await sandbox.get_browser()
    if not browser:
        logger.error(f"Failed to get browser for sandbox {session.sandbox_id}")
        raise RuntimeError(f"Failed to get browser for sandbox {session.sandbox_id}")

    return AgentTaskRunner(
        session_id=session.id,
        agent_id=session.agent_id,
        user_id=session.user_id,
        sandbox=sandbox,
        browser=browser,
        file_storage=get_file_storage(),
        search_engine=get_search_engine(),
        session_repository=session_repository,
        agent_repository=MongoAgentRepository(),
        mcp_repository=FileMCPRepository(),
    )
