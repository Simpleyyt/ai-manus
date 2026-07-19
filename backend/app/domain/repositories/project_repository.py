from typing import Optional, Protocol, List
from app.domain.models.project import Project


class ProjectRepository(Protocol):
    """Repository interface for Project aggregate"""

    async def save(self, project: Project) -> None:
        ...

    async def find_by_id(self, project_id: str) -> Optional[Project]:
        ...

    async def find_by_id_and_user_id(self, project_id: str, user_id: str) -> Optional[Project]:
        ...

    async def find_by_user_id(self, user_id: str) -> List[Project]:
        ...

    async def delete(self, project_id: str) -> None:
        ...

    async def update_pin(self, project_id: str, is_pinned: bool) -> None:
        ...

    async def update_name(self, project_id: str, name: str, instruction: Optional[str] = None) -> None:
        ...
