from fastapi import APIRouter, Depends
from typing import List
from app.application.services.project_service import ProjectService
from app.interfaces.dependencies import get_current_user, get_project_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectItem,
    ListProjectsResponse,
    PinProjectRequest,
)
from app.domain.models.user import User
from app.domain.models.project import Project

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_item(project: Project) -> ProjectItem:
    return ProjectItem(
        project_id=project.id,
        name=project.name,
        instruction=project.instruction,
        is_pinned=project.is_pinned,
        sort_order=project.sort_order,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("", response_model=APIResponse[ListProjectsResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> APIResponse[ListProjectsResponse]:
    projects = await project_service.list_projects(current_user.id)
    return APIResponse.success(ListProjectsResponse(projects=[_to_item(p) for p in projects]))


@router.post("", response_model=APIResponse[ProjectItem])
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> APIResponse[ProjectItem]:
    project = await project_service.create_project(
        current_user.id,
        name=request.name,
        instruction=request.instruction,
    )
    return APIResponse.success(_to_item(project))


@router.patch("/{project_id}", response_model=APIResponse[ProjectItem])
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> APIResponse[ProjectItem]:
    project = await project_service.update_project(
        project_id,
        current_user.id,
        name=request.name,
        instruction=request.instruction,
    )
    return APIResponse.success(_to_item(project))


@router.delete("/{project_id}", response_model=APIResponse[None])
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> APIResponse[None]:
    await project_service.delete_project(project_id, current_user.id)
    return APIResponse.success()


@router.post("/{project_id}/pin", response_model=APIResponse[ProjectItem])
async def pin_project(
    project_id: str,
    request: PinProjectRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> APIResponse[ProjectItem]:
    project = await project_service.pin_project(project_id, current_user.id, request.is_pinned)
    return APIResponse.success(_to_item(project))
