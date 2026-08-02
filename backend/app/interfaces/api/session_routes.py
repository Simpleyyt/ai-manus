from fastapi import APIRouter, Depends
from typing import List, Optional
import logging
from app.interfaces.dependencies import get_file_service

from app.application.services.agent_service import AgentService
from app.application.errors.exceptions import NotFoundError, UnauthorizedError, BadRequestError
from app.interfaces.dependencies import get_agent_service, get_current_user, get_optional_current_user
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.session import (
    ShellViewRequest, CreateSessionResponse, GetSessionResponse,
    ListSessionItem, ListSessionResponse, ShellViewResponse,
    ShareSessionResponse, SharedSessionResponse,
    UpdateSessionTitleRequest, UpdateSessionTitleResponse,
    FavoriteSessionResponse, PinSessionRequest, PinSessionResponse,
    MoveSessionProjectRequest, MoveSessionProjectResponse,
    UpdateSessionTaskModeRequest, UpdateSessionTaskModeResponse,
    LibraryFileItem, LibraryResponse,
)
from app.interfaces.schemas.file import FileViewRequest, FileViewResponse
from app.interfaces.schemas.event import EventMapper
from app.domain.models.file import FileInfo
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.put("", response_model=APIResponse[CreateSessionResponse])
async def create_session(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[CreateSessionResponse]:
    session = await agent_service.create_session(current_user.id)
    return APIResponse.success(
        CreateSessionResponse(
            session_id=session.id,
        )
    )

@router.get("/{session_id}", response_model=APIResponse[GetSessionResponse])
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[GetSessionResponse]:
    session = await agent_service.get_session(session_id, current_user.id)
    if not session:
        raise NotFoundError("Session not found")
    return APIResponse.success(GetSessionResponse(
        session_id=session.id,
        title=session.title,
        status=session.status,
        events=await EventMapper.events_to_stream_events(session.events),
        is_shared=session.is_shared,
        is_favorite=session.is_favorite,
        is_pinned=session.is_pinned,
        project_id=session.project_id,
        task_mode=session.task_mode,
    ))

@router.delete("/{session_id}", response_model=APIResponse[None])
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.delete_session(session_id, current_user.id)
    return APIResponse.success()

@router.patch("/{session_id}/title", response_model=APIResponse[UpdateSessionTitleResponse])
async def update_session_title(
    session_id: str,
    request: UpdateSessionTitleRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[UpdateSessionTitleResponse]:
    title = request.title.strip()
    if not title:
        raise BadRequestError("Title cannot be empty")
    await agent_service.update_session_title(session_id, current_user.id, title)
    return APIResponse.success(UpdateSessionTitleResponse(session_id=session_id, title=title))

@router.post("/{session_id}/favorite", response_model=APIResponse[FavoriteSessionResponse])
async def favorite_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[FavoriteSessionResponse]:
    await agent_service.update_session_favorite(session_id, current_user.id, True)
    return APIResponse.success(FavoriteSessionResponse(session_id=session_id, is_favorite=True))

@router.delete("/{session_id}/favorite", response_model=APIResponse[FavoriteSessionResponse])
async def unfavorite_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[FavoriteSessionResponse]:
    await agent_service.update_session_favorite(session_id, current_user.id, False)
    return APIResponse.success(FavoriteSessionResponse(session_id=session_id, is_favorite=False))

@router.post("/{session_id}/pin", response_model=APIResponse[PinSessionResponse])
async def pin_session(
    session_id: str,
    request: PinSessionRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[PinSessionResponse]:
    await agent_service.update_session_pin(session_id, current_user.id, request.is_pinned)
    return APIResponse.success(PinSessionResponse(session_id=session_id, is_pinned=request.is_pinned))

@router.patch("/{session_id}/project", response_model=APIResponse[MoveSessionProjectResponse])
async def move_session_project(
    session_id: str,
    request: MoveSessionProjectRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[MoveSessionProjectResponse]:
    if request.project_id:
        from app.interfaces.dependencies import get_project_service
        project_service = get_project_service()
        await project_service.get_project(request.project_id, current_user.id)
    await agent_service.update_session_project(session_id, current_user.id, request.project_id)
    return APIResponse.success(MoveSessionProjectResponse(
        session_id=session_id,
        project_id=request.project_id,
    ))

@router.patch("/{session_id}/mode", response_model=APIResponse[UpdateSessionTaskModeResponse])
async def update_session_task_mode(
    session_id: str,
    request: UpdateSessionTaskModeRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> APIResponse[UpdateSessionTaskModeResponse]:
    await agent_service.update_session_task_mode(
        session_id, current_user.id, request.task_mode.value
    )
    return APIResponse.success(UpdateSessionTaskModeResponse(
        session_id=session_id,
        task_mode=request.task_mode,
    ))

@router.post("/{session_id}/stop", response_model=APIResponse[None])
async def stop_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.stop_session(session_id, current_user.id)
    return APIResponse.success()

@router.post("/{session_id}/clear_unread_message_count", response_model=APIResponse[None])
async def clear_unread_message_count(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.clear_unread_message_count(session_id, current_user.id)
    return APIResponse.success()

@router.get("", response_model=APIResponse[ListSessionResponse])
async def get_all_sessions(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ListSessionResponse]:
    summaries = await agent_service.get_all_sessions(current_user.id)
    session_items = [ListSessionItem.from_domain(s) for s in summaries]
    return APIResponse.success(ListSessionResponse(sessions=session_items))

@router.post("/{session_id}/shell")
async def view_shell(
    session_id: str,
    request: ShellViewRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ShellViewResponse]:
    """View shell session output
    
    If the agent does not exist or fails to get shell output, an appropriate exception will be thrown and handled by the global exception handler
    
    Args:
        session_id: Session ID
        request: Shell view request containing session ID
        
    Returns:
        APIResponse with shell output
    """
    result = await agent_service.shell_view(session_id, request.session_id, current_user.id)
    return APIResponse.success(result)

@router.post("/{session_id}/file")
async def view_file(
    session_id: str,
    request: FileViewRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[FileViewResponse]:
    """View file content
    
    If the agent does not exist or fails to get file content, an appropriate exception will be thrown and handled by the global exception handler
    
    Args:
        session_id: Session ID
        request: File view request containing file path
        
    Returns:
        APIResponse with file content
    """
    result = await agent_service.file_view(session_id, request.file, current_user.id)
    return APIResponse.success(result)

@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[List[FileInfo]]:
    if not current_user and not await agent_service.is_session_shared(session_id):
        raise UnauthorizedError()
    files = await agent_service.get_session_files(session_id, current_user.id if current_user else None)
    return APIResponse.success(files)


@router.post("/{session_id}/share", response_model=APIResponse[ShareSessionResponse])
async def share_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ShareSessionResponse]:
    """Share a session to make it publicly accessible
    
    This endpoint marks a session as shared, allowing it to be accessed
    without authentication using the shared session endpoint.
    """
    await agent_service.share_session(session_id, current_user.id)
    return APIResponse.success(ShareSessionResponse(
        session_id=session_id,
        is_shared=True
    ))

@router.get("/{session_id}/share/files")
async def get_shared_session_files(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[List[FileInfo]]:
    files = await agent_service.get_shared_session_files(session_id)
    for file in files:
        await get_file_service().enrich_with_file_url(file)
    return APIResponse.success(files)


@router.delete("/{session_id}/share", response_model=APIResponse[ShareSessionResponse])
async def unshare_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ShareSessionResponse]:
    """Unshare a session to make it private again
    
    This endpoint marks a session as not shared, removing public access.
    """
    await agent_service.unshare_session(session_id, current_user.id)
    return APIResponse.success(ShareSessionResponse(
        session_id=session_id,
        is_shared=False
    ))


@router.get("/shared/{session_id}", response_model=APIResponse[SharedSessionResponse])
async def get_shared_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[SharedSessionResponse]:
    """Get a shared session without authentication
    
    This endpoint allows public access to sessions that have been marked as shared.
    No authentication is required, but the session must be explicitly shared.
    """
    session = await agent_service.get_shared_session(session_id)
    if not session:
        raise NotFoundError("Shared session not found")
    
    return APIResponse.success(SharedSessionResponse(
        session_id=session.id,
        title=session.title,
        status=session.status,
        events=await EventMapper.events_to_stream_events(session.events),
        is_shared=session.is_shared
    ))