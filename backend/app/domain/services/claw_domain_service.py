import re
import secrets
import uuid
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, List

import httpx

from app.domain.models.claw import Claw, ClawStatus, ClawMessage, ClawAttachment
from app.domain.external.claw import ClawRuntime, ClawClient
from app.domain.repositories.claw_repository import ClawRepository

logger = logging.getLogger(__name__)


def _generate_api_key() -> str:
    """Generate a secure per-user API key for LLM proxy authentication"""
    return f"manus-{secrets.token_urlsafe(32)}"


def _generate_claw_id() -> str:
    return str(uuid.uuid4())


class ClawDomainService:
    """Domain service for Claw lifecycle, history merge, and auth logic.

    This service encapsulates pure business rules that are independent of
    application-level concerns (SSE event bus, background task scheduling, etc.).
    """

    def __init__(
        self,
        claw_repository: ClawRepository,
        claw_runtime: ClawRuntime,
        claw_client: ClawClient,
    ):
        self.claw_repository = claw_repository
        self.claw_runtime = claw_runtime
        self.claw_client = claw_client

    # ------------------------------------------------------------------
    # Claw CRUD / lifecycle
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

    async def prepare_claw_for_creation(self, user_id: str) -> Optional[Claw]:
        """Prepare a Claw record for creation (or return existing running one).

        Returns the Claw object ready for async provisioning, or the already-running
        instance. Returns ``None`` only when a new/updated Claw was persisted and the
        caller should kick off ``provision_claw_instance``.
        """
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
        return claw

    async def provision_claw_instance(self, claw: Claw, ttl_seconds: Optional[int] = None) -> None:
        """Provision the underlying claw runtime instance and update the record.

        Intended to be called in a background task after ``prepare_claw_for_creation``.
        """
        try:
            info = await self.claw_runtime.create(claw.id, claw.api_key)
            claw.container_name = info.instance_name
            claw.container_ip = info.address
            if claw.http_base_url:
                ready = await self.claw_runtime.wait_for_ready(claw.http_base_url)
                if not ready:
                    raise RuntimeError(f"Claw service not ready: {claw.http_base_url}")
            logger.info(f"Claw created: id={claw.id} address={info.address}")
            claw.status = ClawStatus.RUNNING
            if ttl_seconds and ttl_seconds > 0:
                claw.expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
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

    async def delete_claw(self, user_id: str) -> bool:
        """Delete the claw record from MongoDB but keep the container alive."""
        claw = await self.claw_repository.get_by_user_id(user_id)
        if not claw:
            return False
        return await self.claw_repository.delete_by_user_id(user_id)

    # ------------------------------------------------------------------
    # History merge
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Chat processing (core streaming logic)
    # ------------------------------------------------------------------

    async def process_chat_stream(
        self, user_id: str, base_url: str, message: str, session_id: str,
    ):
        """Stream chat from the claw client, persisting messages.

        Yields raw chunk dicts from the claw client. The caller is responsible
        for broadcasting chunks to SSE / WebSocket consumers.
        """
        assistant_content: list[str] = []
        file_attachments: list[ClawAttachment] = []

        try:
            async for chunk in self.claw_client.chat_stream(base_url, message, session_id):
                if chunk.get("type") == "text" and chunk.get("content"):
                    assistant_content.append(chunk["content"])

                if chunk.get("type") == "file" and chunk.get("file_id"):
                    file_attachments.append(ClawAttachment(
                        file_id=chunk["file_id"],
                        filename=chunk.get("filename", chunk["file_id"]),
                        content_type=chunk.get("content_type"),
                        size=chunk.get("size", 0),
                        file_url=chunk.get("file_url"),
                    ))

                yield chunk

        finally:
            if file_attachments:
                await self.claw_repository.append_message(
                    user_id, "attachments", "assistant", attachments=file_attachments,
                )
            if assistant_content:
                await self.claw_repository.append_message(
                    user_id, "assistant", "".join(assistant_content),
                )

    async def validate_claw_for_chat(self, user_id: str) -> Claw:
        """Validate that a user has a running claw instance ready for chat.

        Returns the Claw instance or raises ValueError.
        """
        claw = await self.claw_repository.get_by_user_id(user_id)
        if not claw or not claw.http_base_url:
            raise ValueError("No running claw instance found")
        if claw.status != ClawStatus.RUNNING:
            raise ValueError(f"Claw is not running (status: {claw.status})")
        return claw

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

    async def verify_api_key(self, api_key: str, system_api_key: Optional[str] = None) -> Optional[str]:
        """Verify a claw API key and return the associated user ID.

        ``system_api_key`` is an optional global key (from settings) that
        bypasses per-user lookup and returns a fixed service account ID.
        """
        if system_api_key and api_key == system_api_key:
            return "claw-service-account"
        claw = await self.get_claw_by_api_key(api_key)
        if claw:
            return claw.user_id
        return None
