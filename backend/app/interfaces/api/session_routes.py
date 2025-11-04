from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator, List, Optional
from sse_starlette.event import ServerSentEvent
from datetime import datetime
import asyncio
import websockets
import logging
from app.interfaces.dependencies import get_file_service

from app.application.services.agent_service import AgentService
from app.application.services.token_service import TokenService
from app.application.errors.exceptions import NotFoundError, UnauthorizedError
from app.interfaces.dependencies import get_agent_service, get_current_user, get_optional_current_user, get_token_service, verify_signature_websocket
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.session import (
    ChatRequest, ShellViewRequest, CreateSessionResponse, GetSessionResponse,
    ListSessionItem, ListSessionResponse, ShellViewResponse,
    ShareSessionResponse, SharedSessionResponse
)
from app.interfaces.schemas.file import FileViewRequest, FileViewResponse
from app.interfaces.schemas.resource import AccessTokenRequest, SignedUrlResponse
from app.interfaces.schemas.event import EventMapper
from app.domain.models.file import FileInfo
from app.domain.models.user import User

logger = logging.getLogger(__name__)
SESSION_POLL_INTERVAL = 5

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
        events=await EventMapper.events_to_sse_events(session.events),
        is_shared=session.is_shared
    ))

@router.delete("/{session_id}", response_model=APIResponse[None])
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.delete_session(session_id, current_user.id)
    return APIResponse.success()

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
    sessions = await agent_service.get_all_sessions(current_user.id)
    session_items = [
        ListSessionItem(
            session_id=session.id,
            title=session.title,
            status=session.status,
            unread_message_count=session.unread_message_count,
            latest_message=session.latest_message,
            latest_message_at=int(session.latest_message_at.timestamp()) if session.latest_message_at else None,
            is_shared=session.is_shared
        ) for session in sessions
    ]
    return APIResponse.success(ListSessionResponse(sessions=session_items))

@router.post("")
async def stream_sessions(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        while True:
            sessions = await agent_service.get_all_sessions(current_user.id)
            session_items = [
                ListSessionItem(
                    session_id=session.id,
                    title=session.title,
                    status=session.status,
                    unread_message_count=session.unread_message_count,
                    latest_message=session.latest_message,
                    latest_message_at=int(session.latest_message_at.timestamp()) if session.latest_message_at else None,
                    is_shared=session.is_shared
                ) for session in sessions
            ]
            yield ServerSentEvent(
                event="sessions",
                data=ListSessionResponse(sessions=session_items).model_dump_json()
            )
            await asyncio.sleep(SESSION_POLL_INTERVAL)
    return EventSourceResponse(event_generator())

@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        async for event in agent_service.chat(
            session_id=session_id,
            user_id=current_user.id,
            message=request.message,
            timestamp=datetime.fromtimestamp(request.timestamp) if request.timestamp else None,
            event_id=request.event_id,
            attachments=request.attachments
        ):
            logger.debug(f"Received event from chat: {event}")
            sse_event = await EventMapper.event_to_sse_event(event)
            logger.debug(f"Received event: {sse_event}")
            if sse_event:
                yield ServerSentEvent(
                    event=sse_event.event,
                    data=sse_event.data.model_dump_json() if sse_event.data else None
                )

    return EventSourceResponse(event_generator())

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

@router.websocket("/{session_id}/vnc")
async def vnc_websocket(
    websocket: WebSocket,
    session_id: str,
    signature: str = Depends(verify_signature_websocket),
    agent_service: AgentService = Depends(get_agent_service)
) -> None:
    """VNC WebSocket endpoint (binary mode)
    
    Establishes a connection with the VNC WebSocket service in the sandbox environment and forwards data bidirectionally
    Supports authentication via signed URL with signature verification
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID
        signature: Verified signature from dependency injection
    """
    
    await websocket.accept(subprotocol="binary")
    logger.info(f"Accepted WebSocket connection for session {session_id}")
    
    try:
        # Get sandbox environment address with user validation
        sandbox_ws_url = await agent_service.get_vnc_url(session_id)

        logger.info(f"Connecting to VNC WebSocket at {sandbox_ws_url}")
    
        # Connect to sandbox WebSocket
        async with websockets.connect(sandbox_ws_url) as sandbox_ws:
            logger.info(f"Connected to VNC WebSocket at {sandbox_ws_url}")
            # Create two tasks to forward data bidirectionally
            async def forward_to_sandbox():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await sandbox_ws.send(data)
                except WebSocketDisconnect:
                    logger.info("Web -> VNC connection closed")
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding data to sandbox: {e}")
            
            async def forward_from_sandbox():
                try:
                    while True:
                        data = await sandbox_ws.recv()
                        await websocket.send_bytes(data)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("VNC -> Web connection closed")
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding data from sandbox: {e}")
            
            # Run two forwarding tasks concurrently
            forward_task1 = asyncio.create_task(forward_to_sandbox())
            forward_task2 = asyncio.create_task(forward_from_sandbox())
            
            # Wait for either task to complete (meaning connection has closed)
            done, pending = await asyncio.wait(
                [forward_task1, forward_task2],
                return_when=asyncio.FIRST_COMPLETED
            )

            logger.info("WebSocket connection closed")
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
    
    except ConnectionError as e:
        logger.error(f"Unable to connect to sandbox environment: {str(e)}")
        await websocket.close(code=1011, reason=f"Unable to connect to sandbox environment: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason=f"WebSocket error: {str(e)}")

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


@router.post("/{session_id}/vnc/signed-url", response_model=APIResponse[SignedUrlResponse])
async def create_vnc_signed_url(
    session_id: str,
    request_data: AccessTokenRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    token_service: TokenService = Depends(get_token_service)
) -> APIResponse[SignedUrlResponse]:
    """Generate signed URL for VNC WebSocket access
    
    This endpoint creates a signed URL that allows temporary access to the VNC
    WebSocket for a specific session without requiring authentication headers.
    """
    
    # Validate expiration time (max 15 minutes)
    expire_minutes = request_data.expire_minutes
    if expire_minutes > 15:
        expire_minutes = 15
    
    # Check if session exists and belongs to user
    session = await agent_service.get_session(session_id, current_user.id)
    if not session:
        raise NotFoundError("Session not found")
    
    # Create signed URL for VNC WebSocket
    ws_base_url = f"/api/v1/sessions/{session_id}/vnc"
    signed_url = token_service.create_signed_url(
        base_url=ws_base_url,
        expire_minutes=expire_minutes
    )
    
    logger.info(f"Created signed URL for VNC access for user {current_user.id}, session {session_id}")
    
    return APIResponse.success(SignedUrlResponse(
        signed_url=signed_url,
        expires_in=expire_minutes * 60,
    ))


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
        events=await EventMapper.events_to_sse_events(session.events),
        is_shared=session.is_shared
    ))