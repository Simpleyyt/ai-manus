from fastapi import APIRouter, Depends
from app.application.services.agent_service import AgentService
from app.interfaces.dependencies import get_current_user, get_agent_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.session import LibraryFileItem, LibraryResponse
from app.domain.models.user import User

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/files", response_model=APIResponse[LibraryResponse])
async def get_library_files(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[LibraryResponse]:
    files = await agent_service.get_library_files(current_user.id)
    return APIResponse.success(LibraryResponse(files=[LibraryFileItem(**f) for f in files]))
