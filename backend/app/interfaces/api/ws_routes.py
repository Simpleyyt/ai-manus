"""WebSocket routes for realtime session list, chat, and Claw."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import httpx
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.models.claw import ClawAttachment
from app.domain.models.file import FileInfo
from app.interfaces.dependencies import (
    resolve_ws_user,
    get_agent_service,
    get_claw_service,
    get_file_service,
)
from app.interfaces.schemas.event import EventMapper
from app.interfaces.schemas.session import ListSessionItem
from app.infrastructure.storage.redis import get_redis
from app.infrastructure.external.session_list import (
    channel_for_user,
    parse_notify_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["ws"])

SESSION_LIST_KEEPALIVE_SECONDS = 20.0
CHAT_WS_PING_SECONDS = 20.0
CLAW_HEARTBEAT_INTERVAL = 15


@router.websocket("/sessions")
async def sessions_list_ws(websocket: WebSocket):
    """User session list channel.

    Auth: Cookie (browser) or Authorization Bearer (App). No ?token=.

    Server → Client JSON:
      {"op":"snapshot","sessions":[...]}
      {"op":"upsert","session":{...}}
      {"op":"remove","session_id":"..."}
      {"op":"ping"}
    """
    try:
        user = await resolve_ws_user(websocket)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    agent_service = get_agent_service()

    redis = get_redis()
    await redis.initialize()
    channel = channel_for_user(user.id)
    pubsub = redis.client.pubsub()
    await pubsub.subscribe(channel)

    try:
        summaries = await agent_service.get_all_sessions(user.id)
        await websocket.send_json({
            "op": "snapshot",
            "sessions": [
                ListSessionItem.from_domain(s).model_dump(mode="json")
                for s in summaries
            ],
        })

        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=SESSION_LIST_KEEPALIVE_SECONDS,
            )
            if message is None:
                await websocket.send_json({"op": "ping"})
                continue
            if message.get("type") != "message":
                continue
            raw = message.get("data", "")
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8", errors="replace")
            payload = parse_notify_payload(raw)
            if not payload:
                continue
            op = payload["op"]
            session_id = payload["session_id"]
            if op == "remove":
                await websocket.send_json({"op": "remove", "session_id": session_id})
                continue
            summary = await agent_service.get_session_summary(session_id, user.id)
            if summary:
                await websocket.send_json({
                    "op": "upsert",
                    "session": ListSessionItem.from_domain(summary).model_dump(mode="json"),
                })
    except WebSocketDisconnect:
        logger.debug("Session list WS disconnected for user %s", user.id)
    except Exception:
        logger.exception("Session list WS error for user %s", user.id)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            logger.debug("Failed to close session list pubsub", exc_info=True)


@router.websocket("/chat")
async def chat_ws(websocket: WebSocket):
    """Chat channel — one connection per tab; switch sessions via join/leave.

    Auth: Cookie (browser) or Authorization Bearer (App). No ?token=.

    Client → Server:
      {"type":"join_session","session_id":"...","last_event_id":"...?"}
      {"type":"leave_session","session_id":"..."}
      {"type":"chat","session_id":"...","message":"...","attachments":[],"timestamp":123}
      {"type":"stop_session","session_id":"..."}

    Server → Client:
      {"type":"joined","session_id":"..."}
      {"type":"left","session_id":"..."}
      {"type":"event","session_id":"...","event":"message|tool|...","data":{...}}
      {"type":"stream_end","session_id":"..."}
      {"type":"error","error":"...","session_id":"...?"}
      {"type":"ping"}
    """
    try:
        user = await resolve_ws_user(websocket)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    agent_service = get_agent_service()

    joined_session_id: Optional[str] = None
    stream_task: Optional[asyncio.Task] = None
    send_lock = asyncio.Lock()

    async def safe_send(payload: dict[str, Any]) -> None:
        async with send_lock:
            await websocket.send_json(payload)

    async def cancel_stream() -> None:
        nonlocal stream_task
        if stream_task and not stream_task.done():
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.debug("Chat stream task ended with error", exc_info=True)
        stream_task = None

    async def stream_session(
        session_id: str,
        message: Optional[str] = None,
        last_event_id: Optional[str] = None,
        attachments: Optional[list[FileInfo]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        try:
            async for event in agent_service.chat(
                session_id=session_id,
                user_id=user.id,
                message=message,
                timestamp=timestamp,
                event_id=last_event_id,
                attachments=attachments,
            ):
                if joined_session_id != session_id:
                    break
                sse = await EventMapper.event_to_sse_event(event)
                data = sse.data.model_dump(mode="json") if sse.data else {}
                await safe_send({
                    "type": "event",
                    "session_id": session_id,
                    "event": sse.event,
                    "data": data,
                })
            if joined_session_id == session_id:
                await safe_send({"type": "stream_end", "session_id": session_id})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Chat stream failed for session %s", session_id)
            try:
                await safe_send({
                    "type": "error",
                    "session_id": session_id,
                    "error": str(e),
                })
            except Exception:
                pass

    def start_stream(**kwargs: Any) -> None:
        nonlocal stream_task

        async def _run() -> None:
            nonlocal stream_task
            try:
                await stream_session(**kwargs)
            finally:
                stream_task = None

        stream_task = asyncio.create_task(_run())

    try:
        while True:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=CHAT_WS_PING_SECONDS,
                )
            except asyncio.TimeoutError:
                await safe_send({"type": "ping"})
                continue

            msg_type = raw.get("type")
            session_id = raw.get("session_id")

            if msg_type == "join_session":
                if not session_id:
                    await safe_send({"type": "error", "error": "session_id required"})
                    continue
                session = await agent_service.get_session(session_id, user.id)
                if not session:
                    await safe_send({
                        "type": "error",
                        "session_id": session_id,
                        "error": "Session not found",
                    })
                    continue

                if joined_session_id and joined_session_id != session_id:
                    await cancel_stream()
                    prev = joined_session_id
                    joined_session_id = None
                    await safe_send({"type": "left", "session_id": prev})

                joined_session_id = session_id
                last_event_id = raw.get("last_event_id")
                await safe_send({"type": "joined", "session_id": session_id})

                # Resume live stream only while agent is actively running.
                # pending/idle: ack join + stream_end so client clears loading.
                status = getattr(session.status, "value", session.status)
                if status == "running":
                    await cancel_stream()
                    start_stream(
                        session_id=session_id,
                        message=None,
                        last_event_id=last_event_id,
                    )
                else:
                    await safe_send({"type": "stream_end", "session_id": session_id})

            elif msg_type == "leave_session":
                target = session_id or joined_session_id
                if not target:
                    continue
                if joined_session_id == target:
                    await cancel_stream()
                    joined_session_id = None
                    await safe_send({"type": "left", "session_id": target})

            elif msg_type == "chat":
                if not session_id:
                    await safe_send({"type": "error", "error": "session_id required"})
                    continue
                if joined_session_id != session_id:
                    await safe_send({
                        "type": "error",
                        "session_id": session_id,
                        "error": "Not joined to this session",
                    })
                    continue

                message = raw.get("message") or ""
                attachments_raw = raw.get("attachments") or []
                attachments: list[FileInfo] = []
                for item in attachments_raw:
                    if isinstance(item, dict) and item.get("file_id"):
                        attachments.append(
                            FileInfo(
                                file_id=item["file_id"],
                                filename=item.get("filename") or "",
                            )
                        )
                ts = raw.get("timestamp")
                timestamp = datetime.fromtimestamp(ts) if ts else None

                await cancel_stream()
                start_stream(
                    session_id=session_id,
                    message=message or None,
                    last_event_id=raw.get("last_event_id") or raw.get("event_id"),
                    attachments=attachments or None,
                    timestamp=timestamp,
                )

            elif msg_type == "stop_session":
                if not session_id:
                    await safe_send({"type": "error", "error": "session_id required"})
                    continue
                try:
                    await agent_service.stop_session(session_id, user.id)
                    await safe_send({"type": "stopped", "session_id": session_id})
                except Exception as e:
                    await safe_send({
                        "type": "error",
                        "session_id": session_id,
                        "error": str(e),
                    })
            else:
                await safe_send({
                    "type": "error",
                    "error": f"Unknown type: {msg_type}",
                })

    except WebSocketDisconnect:
        logger.debug("Chat WS disconnected for user %s", user.id)
    except Exception:
        logger.exception("Chat WS error for user %s", user.id)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        await cancel_stream()


@router.websocket("/claw")
async def claw_ws(websocket: WebSocket):
    """Claw chat channel — same Cookie / Bearer resolve as /ws/sessions and /ws/chat.

    Client → Server:
      {"type":"chat","message":"...","session_id":"default","file_ids":[]}

    Server → Client:
      {"type":"text","content":"..."}
      {"type":"file",...}
      {"type":"done","stop_reason":"..."}
      {"type":"error","error":"..."}
      {"type":"catchup","content":"..."}
      {"type":"heartbeat"}
    """
    try:
        user = await resolve_ws_user(websocket)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    claw_service = get_claw_service()
    queue = claw_service.event_bus.subscribe(user.id)

    async def _write_events() -> None:
        try:
            pending = claw_service.get_pending_content(user.id)
            if pending:
                await websocket.send_json({"type": "catchup", "content": pending})

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=CLAW_HEARTBEAT_INTERVAL)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "heartbeat"})
        except (WebSocketDisconnect, asyncio.CancelledError, Exception):
            pass

    file_service = get_file_service()

    async def _process_files(
        file_ids: list[str], uid: str
    ) -> tuple[str, list[ClawAttachment]]:
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
                logger.info("[claw-ws] pushed %s to workspace: %s", filename, local_path)

            except Exception as e:
                logger.warning("[claw-ws] failed to process file %s: %s", fid, e)
                refs.append(
                    f'<MANUS_FILE name="{fid}" id="{fid}" status="download_failed" '
                    f'reason="{str(e)[:100]}" />'
                )

        return "\n".join(refs), attachments

    async def _read_messages() -> None:
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
        _done, pending = await asyncio.wait(
            [write_task, read_task], return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
    finally:
        claw_service.event_bus.unsubscribe(user.id, queue)


@router.websocket("/vnc/{session_id}")
async def vnc_ws(websocket: WebSocket, session_id: str):
    """Sandbox VNC proxy (binary) — Cookie / Bearer auth, no signed URL.

    Client should negotiate subprotocol ``binary`` (NoVNC default).
    """
    try:
        user = await resolve_ws_user(websocket)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    agent_service = get_agent_service()
    session = await agent_service.get_session(session_id, user.id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept(subprotocol="binary")
    logger.info("Accepted VNC WS for session %s user %s", session_id, user.id)

    try:
        sandbox_ws_url = await agent_service.get_vnc_url(session_id)
        logger.info("Connecting to sandbox VNC at %s", sandbox_ws_url)

        async with websockets.connect(sandbox_ws_url) as sandbox_ws:
            async def forward_to_sandbox() -> None:
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await sandbox_ws.send(data)
                except WebSocketDisconnect:
                    logger.info("Web -> VNC connection closed")
                except Exception as e:
                    logger.error("Error forwarding data to sandbox: %s", e)

            async def forward_from_sandbox() -> None:
                try:
                    while True:
                        data = await sandbox_ws.recv()
                        await websocket.send_bytes(data)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("VNC -> Web connection closed")
                except Exception as e:
                    logger.error("Error forwarding data from sandbox: %s", e)

            forward_task1 = asyncio.create_task(forward_to_sandbox())
            forward_task2 = asyncio.create_task(forward_from_sandbox())
            _done, pending = await asyncio.wait(
                [forward_task1, forward_task2],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except ConnectionError as e:
        logger.error("Unable to connect to sandbox environment: %s", e)
        try:
            await websocket.close(
                code=1011,
                reason=f"Unable to connect to sandbox environment: {str(e)}",
            )
        except Exception:
            pass
    except Exception as e:
        logger.error("VNC WebSocket error: %s", e)
        try:
            await websocket.close(code=1011, reason=f"WebSocket error: {str(e)}")
        except Exception:
            pass
