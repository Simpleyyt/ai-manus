from fastapi import APIRouter, Depends
from app.application.services.agent_service import AgentService
from app.interfaces.dependencies import get_current_user, get_agent_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.session import (
    LibraryFileItem,
    LibraryResponse,
    FavoriteLibraryFileResponse,
)
from app.domain.models.user import User

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/files", response_model=APIResponse[LibraryResponse])
async def get_library_files(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[LibraryResponse]:
    files = await agent_service.get_library_files(current_user.id)
    return APIResponse.success(LibraryResponse(files=[LibraryFileItem(**f) for f in files]))


@router.post("/files/{file_id}/favorite", response_model=APIResponse[FavoriteLibraryFileResponse])
async def favorite_library_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[FavoriteLibraryFileResponse]:
    await agent_service.update_library_file_favorite(file_id, current_user.id, True)
    return APIResponse.success(FavoriteLibraryFileResponse(file_id=file_id, is_favorite=True))


@router.delete("/files/{file_id}/favorite", response_model=APIResponse[FavoriteLibraryFileResponse])
async def unfavorite_library_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[FavoriteLibraryFileResponse]:
    await agent_service.update_library_file_favorite(file_id, current_user.id, False)
    return APIResponse.success(FavoriteLibraryFileResponse(file_id=file_id, is_favorite=False))
