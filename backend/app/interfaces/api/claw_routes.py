"""
Claw management API routes.
Endpoints for creating, managing, and chatting with OpenClaw instances.
"""
import json
import asyncio
import logging
import httpx
from fastapi import APIRouter, Depends, Header, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import Response

from app.application.services.claw_service import ClawService
from app.application.services.file_service import FileService
from app.application.errors.exceptions import NotFoundError
from app.domain.models.claw import ClawAttachment
from app.interfaces.dependencies import get_current_user, get_claw_service, get_file_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.claw import (
    ClawResponse, ClawApiKeyResponse,
    ClawHistoryResponse, ClawMessageSchema, ClawAttachmentSchema,
)
from app.interfaces.schemas.file import FileInfoResponse
from app.domain.models.user import User
from app.domain.models.user import UserRole
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claw", tags=["claw"])


@router.get("", response_model=APIResponse[ClawResponse])
async def get_claw(
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
) -> APIResponse[ClawResponse]:
    """Get the current user's claw instance"""
    claw = await claw_service.get_claw(current_user.id)
    if not claw:
        raise NotFoundError("No claw instance found")
    return APIResponse.success(ClawResponse.from_claw(claw))


@router.post("", response_model=APIResponse[ClawResponse])
async def create_claw(
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
) -> APIResponse[ClawResponse]:
    """Create a new claw instance for the current user"""
    claw = await claw_service.create_claw(current_user.id)
    return APIResponse.success(ClawResponse.from_claw(claw))


@router.delete("", response_model=APIResponse[dict])
async def delete_claw(
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
) -> APIResponse[dict]:
    """Delete the current user's claw instance"""
    deleted = await claw_service.delete_claw(current_user.id)
    if not deleted:
        raise NotFoundError("No claw instance found")
    return APIResponse.success({})


@router.get("/api-key", response_model=APIResponse[ClawApiKeyResponse])
async def get_api_key(
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
) -> APIResponse[ClawApiKeyResponse]:
    """Get or generate the per-user API key for LLM proxy authentication"""
    api_key = await claw_service.get_or_create_api_key(current_user.id)
    return APIResponse.success(ClawApiKeyResponse(api_key=api_key))


@router.post("/upload", response_model=APIResponse[FileInfoResponse])
async def upload_claw_file(
    file: UploadFile = File(...),
    x_claw_api_key: str = Header(..., alias="X-Claw-Api-Key"),
    claw_service: ClawService = Depends(get_claw_service),
    file_service: FileService = Depends(get_file_service),
) -> APIResponse[FileInfoResponse]:
    """Upload a file from the claw workspace to Manus storage (authenticated by claw API key)"""
    user_id = await claw_service.verify_api_key(x_claw_api_key)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid claw API key")
    result = await file_service.upload_file(
        file_data=file.file,
        filename=file.filename or "file",
        user_id=user_id,
        content_type=file.content_type,
    )
    return APIResponse.success(await FileInfoResponse.from_file_info(result))


@router.get("/files/{filename}")
async def download_claw_file(
    filename: str,
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
):
    """Proxy a file download from the user's claw workspace"""
    try:
        content, content_type = await claw_service.get_file(current_user.id, filename)
        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[claw-file] Failed to proxy file {filename}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch file from claw")


@router.get("/resolve/{file_id}")
async def resolve_claw_file_meta(
    file_id: str,
    x_claw_api_key: str = Header(..., alias="X-Claw-Api-Key"),
    claw_service: ClawService = Depends(get_claw_service),
    file_service: FileService = Depends(get_file_service),
) -> APIResponse[FileInfoResponse]:
    """Get file metadata for manus-file:// resolution (authenticated by claw API key)"""
    user_id = await claw_service.verify_api_key(x_claw_api_key)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid claw API key")
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise NotFoundError("File not found")
    return APIResponse.success(await FileInfoResponse.from_file_info(file_info))


@router.get("/resolve/{file_id}/download")
async def resolve_claw_file_download(
    file_id: str,
    x_claw_api_key: str = Header(..., alias="X-Claw-Api-Key"),
    claw_service: ClawService = Depends(get_claw_service),
    file_service: FileService = Depends(get_file_service),
):
    """Download file content for manus-file:// resolution (authenticated by claw API key)"""
    user_id = await claw_service.verify_api_key(x_claw_api_key)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid claw API key")
    try:
        file_data, file_info = await file_service.download_file(file_id)
    except (FileNotFoundError, PermissionError):
        raise NotFoundError("File not found")
    import urllib.parse
    encoded_filename = urllib.parse.quote(file_info.filename, safe='')
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        file_data,
        media_type=file_info.content_type or 'application/octet-stream',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/history", response_model=APIResponse[ClawHistoryResponse])
async def get_history(
    current_user: User = Depends(get_current_user),
    claw_service: ClawService = Depends(get_claw_service),
    file_service: FileService = Depends(get_file_service),
) -> APIResponse[ClawHistoryResponse]:
    """Get chat history for the current user's claw"""
    raw_messages = await claw_service.get_history(current_user.id)
    schemas = []
    for m in raw_messages:
        schema = ClawMessageSchema.from_domain(m)
        if schema.attachments:
            for att in schema.attachments:
                try:
                    att.file_url = await file_service.create_signed_url(att.file_id)
                except Exception:
                    pass
        schemas.append(schema)
    return APIResponse.success(ClawHistoryResponse(messages=schemas))


# ---------------------------------------------------------------
# WebSocket: bidirectional channel for chat messages & events
# ---------------------------------------------------------------

HEARTBEAT_INTERVAL = 15

async def _resolve_ws_user(token: str | None) -> User:
    """Resolve User for a WebSocket connection.
    In dev mode (auth_provider=none) returns anonymous; otherwise validates token."""
    settings = get_settings()
    if settings.auth_provider == "none":
        return User(
            id="anonymous", fullname="anonymous",
            email="anonymous@localhost", role=UserRole.USER, is_active=True,
        )
    if not token:
        raise ValueError("Authentication required")
    from app.interfaces.dependencies import get_auth_service
    auth_service = get_auth_service()
    return await auth_service.verify_token(token)


@router.websocket("/ws")
async def claw_ws(websocket: WebSocket, token: str | None = None):
    """Persistent WebSocket connection for Claw chat.

    Client → Server (JSON):
        {"type": "chat", "message": "...", "session_id": "default"}

    Server → Client (JSON):
        {"type": "text", "content": "..."}
        {"type": "file", "file_id": "...", ...}
        {"type": "done", "stop_reason": "end_turn"}
        {"type": "error", "error": "..."}
        {"type": "catchup", "content": "..."}   (on reconnect while response in-progress)
        {"type": "heartbeat"}
    """
    try:
        user = await _resolve_ws_user(token)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    claw_service: ClawService = get_claw_service()
    queue = claw_service.event_bus.subscribe(user.id)

    async def _write_events():
        """Forward events from the bus to the WS client + periodic heartbeat."""
        try:
            # Catch-up for in-progress response
            pending = claw_service.get_pending_content(user.id)
            if pending:
                await websocket.send_json({"type": "catchup", "content": pending})

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "heartbeat"})
        except (WebSocketDisconnect, asyncio.CancelledError, Exception):
            pass

    file_service: FileService = get_file_service()

    async def _process_files(file_ids: list[str], uid: str) -> tuple[str, list[ClawAttachment]]:
        """Download files from GridFS, push to Claw workspace, return
        (MANUS_FILE reference tags for the message, attachment metadata for history).

        Mirrors kimi-claw's file resolution: download → save to workspace → reference tag.
        """
        claw = await claw_service.claw_repository.get_by_user_id(uid)
        claw_base_url = claw.http_base_url if claw else None

        refs: list[str] = []
        attachments: list[ClawAttachment] = []
        for fid in file_ids:
            try:
                stream, info = await file_service.download_file(fid, uid)
                ct = info.content_type or ""
                filename = info.filename or fid
                raw = stream.read() if hasattr(stream, "read") else b""

                attachments.append(ClawAttachment(
                    file_id=fid, filename=filename,
                    content_type=ct, size=info.size or 0,
                ))

                if not claw_base_url:
                    refs.append(f'<MANUS_FILE name="{filename}" id="{fid}" status="no_claw" />')
                    continue

                # Push file to Claw workspace
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{claw_base_url}/workspace",
                        params={"file_id": fid, "filename": filename},
                        content=raw,
                        headers={"Content-Type": "application/octet-stream"},
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    local_path = result.get("path", "")

                refs.append(
                    f'<MANUS_FILE path="{local_path}" name="{filename}" '
                    f'id="{fid}" type="{ct}" size="{info.size}" />'
                )
                logger.info(f"[claw-ws] pushed {filename} to workspace: {local_path}")

            except Exception as e:
                logger.warning(f"[claw-ws] failed to process file {fid}: {e}")
                refs.append(
                    f'<MANUS_FILE name="{fid}" id="{fid}" status="download_failed" '
                    f'reason="{str(e)[:100]}" />'
                )

        return "\n".join(refs), attachments

    async def _read_messages():
        """Read messages from the WS client and dispatch them."""
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                if msg_type == "chat":
                    message = data.get("message", "").strip()
                    session_id = data.get("session_id", "default")
                    file_ids = data.get("file_ids", [])
                    user_attachments: list[ClawAttachment] = []

                    if file_ids:
                        file_refs, user_attachments = await _process_files(file_ids, user.id)
                        if file_refs:
                            message = f"{message}\n\n{file_refs}" if message else file_refs

                    if message:
                        try:
                            await claw_service.send_message(user.id, message, session_id)
                            if user_attachments:
                                await claw_service.claw_repository.append_message(
                                    user.id, "attachments", "user", attachments=user_attachments,
                                )
                        except Exception as e:
                            await websocket.send_json({"type": "error", "error": str(e)})
        except (WebSocketDisconnect, asyncio.CancelledError, Exception):
            pass

    write_task = asyncio.create_task(_write_events())
    read_task = asyncio.create_task(_read_messages())

    try:
        done, pending = await asyncio.wait(
            [write_task, read_task], return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
    finally:
        claw_service.event_bus.unsubscribe(user.id, queue)
