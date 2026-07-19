from typing import List, Optional
from datetime import datetime, UTC
import logging

from app.domain.models.project import Project
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.session_repository import SessionRepository
from app.application.errors.exceptions import NotFoundError, BadRequestError

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        session_repository: SessionRepository,
    ):
        self._project_repository = project_repository
        self._session_repository = session_repository

    async def list_projects(self, user_id: str) -> List[Project]:
        return await self._project_repository.find_by_user_id(user_id)

    async def create_project(
        self,
        user_id: str,
        name: str,
        instruction: Optional[str] = None,
    ) -> Project:
        name = name.strip()
        if not name:
            raise BadRequestError("Project name cannot be empty")
        project = Project(
            user_id=user_id,
            name=name,
            instruction=instruction.strip() if instruction else None,
        )
        await self._project_repository.save(project)
        logger.info(f"Created project {project.id} for user {user_id}")
        return project

    async def update_project(
        self,
        project_id: str,
        user_id: str,
        name: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> Project:
        project = await self._get_owned_project(project_id, user_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise BadRequestError("Project name cannot be empty")
            project.name = name
        if instruction is not None:
            project.instruction = instruction.strip() or None
        project.updated_at = datetime.now(UTC)
        await self._project_repository.save(project)
        return project

    async def delete_project(self, project_id: str, user_id: str) -> None:
        await self._get_owned_project(project_id, user_id)
        await self._session_repository.clear_project_id(project_id)
        await self._project_repository.delete(project_id)
        logger.info(f"Deleted project {project_id} for user {user_id}")

    async def pin_project(self, project_id: str, user_id: str, is_pinned: bool) -> Project:
        project = await self._get_owned_project(project_id, user_id)
        await self._project_repository.update_pin(project_id, is_pinned)
        project.is_pinned = is_pinned
        return project

    async def get_project(self, project_id: str, user_id: str) -> Project:
        return await self._get_owned_project(project_id, user_id)

    async def _get_owned_project(self, project_id: str, user_id: str) -> Project:
        project = await self._project_repository.find_by_id_and_user_id(project_id, user_id)
        if not project:
            raise NotFoundError("Project not found")
        return project
