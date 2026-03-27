import re
import secrets
import uuid
import logging
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, UTC
from typing import Optional, List

import httpx

from app.domain.models.claw import Claw, ClawStatus, ClawMessage, ClawAttachment
from app.domain.external.claw import ClawRuntime, ClawClient
from app.infrastructure.repositories.claw_repository import ClawRepository
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _generate_api_key() -> str:
    """Generate a secure per-user API key for LLM proxy authentication"""
    return f"manus-{secrets.token_urlsafe(32)}"


def _generate_claw_id() -> str:
    return str(uuid.uuid4())


class ClawEventBus:
    """Simple in-memory pub/sub per user for broadcasting SSE events."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, user_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[user_id].append(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue):
        subs = self._subscribers.get(user_id)
        if subs:
            self._subscribers[user_id] = [q for q in subs if q is not queue]

    async def publish(self, user_id: str, event: dict):
        for queue in self._subscribers.get(user_id, []):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass


class _ChatState:
    """Tracks an in-progress response so new SSE clients can catch up."""
    __slots__ = ("pending_text",)

    def __init__(self):
        self.pending_text = ""


class ClawService:
    """Service for managing OpenClaw instances"""

    def __init__(
        self,
        claw_repository: ClawRepository,
        claw_runtime: ClawRuntime,
        claw_client: ClawClient,
    ):
        self.claw_repository = claw_repository
        self.claw_runtime = claw_runtime
        self.claw_client = claw_client
        self.settings = get_settings()
        self._active_user_id: Optional[str] = None
        self.event_bus = ClawEventBus()
        self._bg_tasks: set[asyncio.Task] = set()
        self._chat_states: dict[str, _ChatState] = {}

    # ------------------------------------------------------------------
    # Claw CRUD
    # ------------------------------------------------------------------

    async def get_or_create_api_key(self, user_id: str) -> str:
        claw = await self.claw_repository.get_by_user_id(user_id)
        if claw:
            return claw.api_key
        claw = Claw(
            id=_generate_claw_id(),
            user_id=user_id,
            api_key=_generate_api_key(),
            status=ClawStatus.STOPPED,
        )
        created = await self.claw_repository.create(claw)
        return created.api_key

    async def get_claw(self, user_id: str) -> Optional[Claw]:
        claw = await self.claw_repository.get_by_user_id(user_id)
        if claw and claw.status == ClawStatus.RUNNING:
            expires = claw.expires_at.replace(tzinfo=UTC) if claw.expires_at and claw.expires_at.tzinfo is None else claw.expires_at
            if expires and datetime.now(UTC) >= expires:
                logger.info(f"[claw] expired for user={user_id}, auto-deleting")
                await self.claw_repository.delete_by_user_id(user_id)
                return None
            elif claw.http_base_url and not await self._health_check(claw.http_base_url):
                logger.warning(f"[claw] health check failed for user={user_id}, marking stopped")
                claw.status = ClawStatus.STOPPED
                await self.claw_repository.update(claw)
        return claw

    @staticmethod
    async def _health_check(base_url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def get_claw_by_api_key(self, api_key: str) -> Optional[Claw]:
        return await self.claw_repository.get_by_api_key(api_key)

    async def create_claw(self, user_id: str) -> Claw:
        existing = await self.claw_repository.get_by_user_id(user_id)
        if existing and existing.status == ClawStatus.RUNNING:
            return existing

        if existing:
            api_key = existing.api_key
            claw_id = existing.id
        else:
            api_key = _generate_api_key()
            claw_id = _generate_claw_id()

        claw = Claw(
            id=claw_id,
            user_id=user_id,
            api_key=api_key,
            status=ClawStatus.CREATING,
        )
        if existing:
            claw = await self.claw_repository.update(claw)
        else:
            claw = await self.claw_repository.create(claw)
        task = asyncio.create_task(self._create_claw_instance(claw))
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)
        return claw

    async def _create_claw_instance(self, claw: Claw) -> None:
        try:
            info = await self.claw_runtime.create(claw.id, claw.api_key)
            claw.container_name = info.instance_name
            claw.container_ip = info.address
            if claw.http_base_url:
                ready = await self.claw_runtime.wait_for_ready(claw.http_base_url)
                if not ready:
                    raise RuntimeError(f"Claw service not ready: {claw.http_base_url}")
            logger.info(
                f"Claw created: id={claw.id} address={info.address}"
            )
            claw.status = ClawStatus.RUNNING
            ttl = self.settings.claw_ttl_seconds
            if ttl and ttl > 0:
                claw.expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
            await self.claw_repository.update(claw)
            await self.claw_repository.append_message(
                claw.user_id, "assistant", "i18n:Claw is ready, let's chat!",
            )
        except Exception as e:
            logger.error(f"Failed to create claw instance: {e}")
            claw.status = ClawStatus.ERROR
            claw.error_message = str(e)
            try:
                await self.claw_repository.update(claw)
            except Exception:
                pass

    async def get_history(self, user_id: str) -> List[ClawMessage]:
        """Merge MongoDB messages with OpenClaw's native session history."""
        db_msgs = await self.claw_repository.get_messages(user_id)

        claw_msgs: List[ClawMessage] = []
        try:
            claw = await self.claw_repository.get_by_user_id(user_id)
            if claw and claw.http_base_url and claw.status == ClawStatus.RUNNING:
                claw_msgs = await self.claw_client.get_history(
                    claw.http_base_url, "default", 200,
                )
        except Exception as e:
            logger.warning(f"[claw-history] failed to fetch claw native history: {e}")

        if not claw_msgs:
            return db_msgs

        return self._merge_histories(db_msgs, claw_msgs)

    @staticmethod
    def _normalize_ts(ts: int) -> int:
        """Normalize timestamp to seconds (Claw uses ms, MongoDB uses seconds)."""
        if ts > 1_000_000_000_000:
            return ts // 1000
        return ts

    @staticmethod
    def _strip_openclaw_prefix(text: str) -> str:
        """Strip OpenClaw's timestamp prefix like '[Sat 2026-03-21 11:11 UTC] '."""
        return re.sub(r'^\[.*?\]\s*', '', text)

    @classmethod
    def _normalize_content(cls, text: str) -> str:
        """Normalize message text for dedup comparison."""
        text = cls._strip_openclaw_prefix(text)
        text = re.sub(r'<MANUS_FILE\b[^>]*/>', '', text)
        return text.strip()

    @classmethod
    def _merge_histories(
        cls, db_msgs: List[ClawMessage], claw_msgs: List[ClawMessage],
    ) -> List[ClawMessage]:
        """Merge two message lists, dedup, return sorted by timestamp.

        DB messages are authoritative; Claw messages fill gaps.
        Uses (role, timestamp proximity, content prefix) for cross-source dedup
        so that identical messages sent at different times are kept distinct.
        Attachment messages are deduped by file_id.
        """

        TS_WINDOW = 5  # seconds tolerance between DB and Claw timestamps

        seen_file_ids: set[str] = set()
        for m in db_msgs:
            if m.role == "attachments" and m.attachments:
                for att in m.attachments:
                    if att.file_id:
                        seen_file_ids.add(att.file_id)

        db_fingerprints: list[tuple[str, int, str, bool]] = []
        for m in db_msgs:
            if m.role != "attachments":
                norm = cls._normalize_content(m.content or "")
                db_fingerprints.append((m.role, m.timestamp or 0, norm[:120], False))

        merged: List[ClawMessage] = list(db_msgs)

        for m in claw_msgs:
            ts = cls._normalize_ts(m.timestamp or 0)
            content = cls._normalize_content(m.content or "")

            if m.attachments:
                new_atts = [a for a in m.attachments if a.file_id and a.file_id not in seen_file_ids]
                if new_atts:
                    for a in new_atts:
                        seen_file_ids.add(a.file_id)
                    att_role = "user" if m.role == "user" else "assistant"
                    merged.append(ClawMessage(
                        role="attachments", content=att_role,
                        timestamp=ts, attachments=new_atts,
                    ))

            if not content:
                continue

            prefix = content[:120]
            matched = False
            for idx, (fp_role, fp_ts, fp_prefix, fp_used) in enumerate(db_fingerprints):
                if fp_used:
                    continue
                if fp_role != m.role:
                    continue
                if abs(fp_ts - ts) > TS_WINDOW:
                    continue
                if fp_prefix == prefix:
                    db_fingerprints[idx] = (fp_role, fp_ts, fp_prefix, True)
                    matched = True
                    break

            if not matched:
                merged.append(ClawMessage(
                    role=m.role, content=content, timestamp=ts,
                ))

        merged.sort(key=lambda m: m.timestamp or 0)
        return merged

    async def delete_claw(self, user_id: str) -> bool:
        """Delete the claw record from MongoDB but keep the container alive.

        The container preserves its internal session history (.jsonl) so that
        text messages can be recovered after re-creation via the merge pipeline.
        MongoDB messages (including file attachment metadata) are cleared.
        """
        claw = await self.claw_repository.get_by_user_id(user_id)
        if not claw:
            return False
        return await self.claw_repository.delete_by_user_id(user_id)

    # ------------------------------------------------------------------
    # Chat  – fire-and-forget + event bus
    # ------------------------------------------------------------------

    async def send_message(self, user_id: str, message: str, session_id: str = "default") -> None:
        """Accept a user message and kick off background processing.
        Returns immediately; events are broadcast via the event bus."""
        self._active_user_id = user_id

        claw = await self.claw_repository.get_by_user_id(user_id)
        if not claw or not claw.http_base_url:
            raise ValueError("No running claw instance found")
        if claw.status != ClawStatus.RUNNING:
            raise ValueError(f"Claw is not running (status: {claw.status})")

        await self.claw_repository.append_message(user_id, "user", message)

        task = asyncio.create_task(
            self._process_chat(user_id, claw.http_base_url, message, session_id)
        )
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    async def _process_chat(
        self, user_id: str, base_url: str, message: str, session_id: str
    ) -> None:
        """Background task: stream from claw, broadcast events, persist."""
        state = _ChatState()
        self._chat_states[user_id] = state

        assistant_content: list[str] = []
        file_attachments: list[ClawAttachment] = []

        try:
            async for chunk in self.claw_client.chat_stream(base_url, message, session_id):
                if chunk.get("type") == "text" and chunk.get("content"):
                    assistant_content.append(chunk["content"])
                    state.pending_text += chunk["content"]

                if chunk.get("type") == "file" and chunk.get("file_id"):
                    file_attachments.append(ClawAttachment(
                        file_id=chunk["file_id"],
                        filename=chunk.get("filename", chunk["file_id"]),
                        content_type=chunk.get("content_type"),
                        size=chunk.get("size", 0),
                        file_url=chunk.get("file_url"),
                    ))

                if chunk.get("type") != "done":
                    await self.event_bus.publish(user_id, chunk)

        except Exception as e:
            logger.error(f"[claw-chat] background processing error for user={user_id}: {e}")
            await self.event_bus.publish(user_id, {"type": "error", "error": str(e)})
        finally:
            if file_attachments:
                await self.claw_repository.append_message(
                    user_id, "attachments", "assistant", attachments=file_attachments
                )
            if assistant_content:
                await self.claw_repository.append_message(
                    user_id, "assistant", "".join(assistant_content)
                )
            await self.event_bus.publish(user_id, {"type": "done", "stop_reason": "end_turn"})
            self._chat_states.pop(user_id, None)

    def get_pending_content(self, user_id: str) -> Optional[str]:
        """Return accumulated text for an in-progress response (for SSE catch-up)."""
        state = self._chat_states.get(user_id)
        if state and state.pending_text:
            return state.pending_text
        return None

    def is_processing(self, user_id: str) -> bool:
        return user_id in self._chat_states

    # ------------------------------------------------------------------
    # File proxy
    # ------------------------------------------------------------------

    async def get_file(self, user_id: str, filename: str) -> tuple[bytes, str]:
        claw = await self.claw_repository.get_by_user_id(user_id)
        if not claw or not claw.http_base_url:
            raise ValueError("No running claw instance found")
        if claw.status != ClawStatus.RUNNING:
            raise ValueError(f"Claw is not running (status: {claw.status})")
        return await self.claw_client.get_file(claw.http_base_url, filename)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_active_user_id(self) -> Optional[str]:
        return self._active_user_id

    async def verify_api_key(self, api_key: str) -> Optional[str]:
        if self.settings.claw_api_key and api_key == self.settings.claw_api_key:
            return "claw-service-account"
        claw = await self.get_claw_by_api_key(api_key)
        if claw:
            return claw.user_id
        return None
