"""WebSocket routes for realtime session list, chat, and VNC."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.models.file import FileInfo
from app.interfaces.dependencies import (
    resolve_ws_user,
    get_agent_service,
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

# Chat WS protocol (aligned with official Manus control-plane contract).
CHAT_WS_PROTOCOL_VERSION = 2
ERR_BAD_VERSION = 4000
ERR_BAD_REQUEST = 4002
ERR_NOT_FOUND = 4004
ERR_NOT_JOINED = 4009
ERR_INTERNAL = 5000


def _session_status_value(status: Any) -> str:
    return getattr(status, "value", status) if status is not None else "pending"


def _agent_status_from_session(status: Any) -> str:
    """Map SessionStatus → wire agent_status (pending|running|waiting|completed|error)."""
    value = _session_status_value(status)
    if value in ("pending", "running", "waiting", "completed"):
        return value
    return "completed"


def _final_agent_status(
    session_status: Any,
    *,
    saw_wait: bool = False,
    saw_error: bool = False,
) -> str:
    """Resolve end-of-stream agent_status.

    Prefer an in-stream WaitEvent over Mongo: the runner may still be
    RUNNING when WaitEvent is drained, and a trailing status_update of
    "running" would hide the waiting footer.
    """
    if saw_wait or _session_status_value(session_status) == "waiting":
        return "waiting"
    if saw_error:
        return "error"
    return _agent_status_from_session(session_status)


def _events_after(events: list[Any], last_event_id: Optional[str]) -> list[Any]:
    """Return domain events strictly after last_event_id (Mongo catch-up)."""
    if not events:
        return []
    if not last_event_id:
        return list(events)
    idx = next((i for i, e in enumerate(events) if getattr(e, "id", None) == last_event_id), None)
    if idx is None:
        return list(events)
    return list(events[idx + 1 :])


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
    Protocol version: client frames must include ``version: 2``.

    Client → Server (envelope):
      {
        "id": "...", "timestamp": 1710000000, "version": 2,
        "type": "join_session|leave_session|chat|stop_session",
        "session_id": "...",
        "last_event_id": "...?", "message": "...?", "attachments": [],
        "conn_id": "...?"
      }

    Server → Client:
      {"type":"joined|left|stopped","session_id":"...","request_id":"...?"}
      {"type":"ack","request_id":"...","op":"chat","session_id":"...","ok":true}
      {"type":"event","session_id":"...","event":"message|status_update|...","data":{...}}
      {"type":"stream_end","session_id":"..."}
      {"type":"error","error":"...","code":4000,"session_id":"...?","request_id":"...?"}
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

    async def send_error(
        error: str,
        *,
        code: int = ERR_INTERNAL,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        payload: dict[str, Any] = {"type": "error", "error": error, "code": code}
        if session_id:
            payload["session_id"] = session_id
        if request_id:
            payload["request_id"] = request_id
        await safe_send(payload)

    async def send_status_update(session_id: str, agent_status: str) -> None:
        await safe_send({
            "type": "event",
            "session_id": session_id,
            "event": "status_update",
            "data": {
                "event_id": f"status-{session_id}-{agent_status}-{int(datetime.now().timestamp())}",
                "timestamp": int(datetime.now().timestamp()),
                "agent_status": agent_status,
            },
        })

    async def send_agent_event(session_id: str, event: Any) -> None:
        stream_event = await EventMapper.event_to_stream_event(event)
        data = stream_event.data.model_dump(mode="json") if stream_event.data else {}
        await safe_send({
            "type": "event",
            "session_id": session_id,
            "event": stream_event.event,
            "data": data,
        })

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
        saw_error = False
        saw_wait = False
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
                if getattr(event, "type", None) == "error":
                    saw_error = True
                await send_agent_event(session_id, event)
                # Mid-stream phase: WaitEvent — tell clients immediately so phase UI
                # does not depend on domain→phase fallbacks or Mongo lag.
                if getattr(event, "type", None) == "wait":
                    saw_wait = True
                    await send_status_update(session_id, "waiting")
            if joined_session_id == session_id:
                session = await agent_service.get_session(session_id, user.id)
                # Prefer in-stream WaitEvent over Mongo (may still be RUNNING) and
                # over saw_error — early tool errors can coexist with a later wait.
                # Send status_update BEFORE stream_end: clients often clear handlers on
                # stream_end, which would drop a trailing status_update.
                await send_status_update(
                    session_id,
                    _final_agent_status(
                        session.status if session else "completed",
                        saw_wait=saw_wait,
                        saw_error=saw_error,
                    ),
                )
                await safe_send({"type": "stream_end", "session_id": session_id})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Chat stream failed for session %s", session_id)
            try:
                await send_error(str(e), code=ERR_INTERNAL, session_id=session_id)
                if joined_session_id == session_id:
                    await send_status_update(session_id, "error")
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

            if not isinstance(raw, dict):
                await send_error("Invalid message", code=ERR_BAD_REQUEST)
                continue

            msg_type = raw.get("type")
            session_id = raw.get("session_id")
            request_id = raw.get("id")

            # leave_session: still accept missing version (tab-close races), but
            # clients should send version: 2 like other control frames.
            if msg_type != "leave_session" and raw.get("version") != CHAT_WS_PROTOCOL_VERSION:
                await send_error(
                    f"Unsupported protocol version (require {CHAT_WS_PROTOCOL_VERSION})",
                    code=ERR_BAD_VERSION,
                    session_id=session_id,
                    request_id=request_id,
                )
                continue

            if msg_type == "join_session":
                if not session_id:
                    await send_error(
                        "session_id required",
                        code=ERR_BAD_REQUEST,
                        request_id=request_id,
                    )
                    continue
                session = await agent_service.get_session(session_id, user.id)
                if not session:
                    await send_error(
                        "Session not found",
                        code=ERR_NOT_FOUND,
                        session_id=session_id,
                        request_id=request_id,
                    )
                    continue

                if joined_session_id and joined_session_id != session_id:
                    await cancel_stream()
                    prev = joined_session_id
                    joined_session_id = None
                    await safe_send({"type": "left", "session_id": prev})

                joined_session_id = session_id
                last_event_id = raw.get("last_event_id")
                joined_payload: dict[str, Any] = {
                    "type": "joined",
                    "session_id": session_id,
                }
                if request_id:
                    joined_payload["request_id"] = request_id
                await safe_send(joined_payload)

                status = _session_status_value(session.status)
                agent_status = _agent_status_from_session(session.status)

                # Idle/pending/completed/waiting: Mongo catch-up after cursor,
                # then authoritative status_update. Do NOT send stream_end —
                # a follow-up chat would otherwise clear client "thinking".
                if status == "running":
                    await send_status_update(session_id, "running")
                    await cancel_stream()
                    start_stream(
                        session_id=session_id,
                        message=None,
                        last_event_id=last_event_id,
                    )
                else:
                    if last_event_id:
                        for event in _events_after(session.events or [], last_event_id):
                            if joined_session_id != session_id:
                                break
                            await send_agent_event(session_id, event)
                    await send_status_update(session_id, agent_status)

            elif msg_type == "leave_session":
                target = session_id or joined_session_id
                if not target:
                    continue
                if joined_session_id == target:
                    await cancel_stream()
                    joined_session_id = None
                    left_payload: dict[str, Any] = {
                        "type": "left",
                        "session_id": target,
                    }
                    if request_id:
                        left_payload["request_id"] = request_id
                    await safe_send(left_payload)

            elif msg_type == "chat":
                if not session_id:
                    await send_error(
                        "session_id required",
                        code=ERR_BAD_REQUEST,
                        request_id=request_id,
                    )
                    continue
                if joined_session_id != session_id:
                    await send_error(
                        "Not joined to this session",
                        code=ERR_NOT_JOINED,
                        session_id=session_id,
                        request_id=request_id,
                    )
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
                timestamp = datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else None

                if request_id:
                    await safe_send({
                        "type": "ack",
                        "request_id": request_id,
                        "op": "chat",
                        "session_id": session_id,
                        "ok": True,
                    })
                await send_status_update(session_id, "running")
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
                    await send_error(
                        "session_id required",
                        code=ERR_BAD_REQUEST,
                        request_id=request_id,
                    )
                    continue
                try:
                    await agent_service.stop_session(session_id, user.id)
                    stopped_payload: dict[str, Any] = {
                        "type": "stopped",
                        "session_id": session_id,
                    }
                    if request_id:
                        stopped_payload["request_id"] = request_id
                    await safe_send(stopped_payload)
                    await send_status_update(session_id, "completed")
                except Exception as e:
                    await send_error(
                        str(e),
                        code=ERR_INTERNAL,
                        session_id=session_id,
                        request_id=request_id,
                    )
            else:
                await send_error(
                    f"Unknown type: {msg_type}",
                    code=ERR_BAD_REQUEST,
                    request_id=request_id,
                )

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
