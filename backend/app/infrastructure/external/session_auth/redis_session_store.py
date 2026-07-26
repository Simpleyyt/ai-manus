"""Redis implementation of SessionStore for opaque auth sessions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from app.domain.models.auth_session import AuthSession
from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)

SESSION_KEY_PREFIX = "session:"
USER_SESSIONS_KEY_PREFIX = "user_sessions:"


class RedisSessionStore:
    """Redis-backed auth session store with per-user index for revoke-all."""

    def __init__(self) -> None:
        self._redis = get_redis()

    def _session_key(self, session_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{session_id}"

    def _user_index_key(self, user_id: str) -> str:
        return f"{USER_SESSIONS_KEY_PREFIX}{user_id}"

    async def create(self, session: AuthSession, ttl_seconds: int) -> None:
        await self._redis.initialize()
        client = self._redis.client
        key = self._session_key(session.session_id)
        payload = session.model_dump_json()
        pipe = client.pipeline()
        pipe.setex(key, max(1, ttl_seconds), payload)
        pipe.sadd(self._user_index_key(session.user_id), session.session_id)
        await pipe.execute()

    async def get(self, session_id: str) -> Optional[AuthSession]:
        await self._redis.initialize()
        raw = await self._redis.client.get(self._session_key(session_id))
        if not raw:
            return None
        try:
            return AuthSession.model_validate_json(raw)
        except Exception:
            logger.warning("Corrupt auth session payload for %s", session_id)
            await self.delete(session_id)
            return None

    async def touch(self, session_id: str, ttl_seconds: int) -> Optional[AuthSession]:
        session = await self.get(session_id)
        if not session:
            return None
        now = datetime.now(UTC)
        session.last_seen_at = now
        session.expires_at = now + timedelta(seconds=max(1, ttl_seconds))
        await self._redis.initialize()
        await self._redis.client.setex(
            self._session_key(session_id),
            max(1, ttl_seconds),
            session.model_dump_json(),
        )
        return session

    async def delete(self, session_id: str) -> bool:
        session = await self.get(session_id)
        await self._redis.initialize()
        client = self._redis.client
        deleted = await client.delete(self._session_key(session_id))
        if session:
            await client.srem(self._user_index_key(session.user_id), session_id)
        return deleted > 0

    async def delete_all_for_user(self, user_id: str) -> int:
        await self._redis.initialize()
        client = self._redis.client
        index_key = self._user_index_key(user_id)
        session_ids = await client.smembers(index_key)
        if not session_ids:
            return 0
        keys = [self._session_key(sid) for sid in session_ids]
        pipe = client.pipeline()
        pipe.delete(*keys)
        pipe.delete(index_key)
        results = await pipe.execute()
        return int(results[0] or 0)

    async def list_ids_for_user(self, user_id: str) -> list[str]:
        await self._redis.initialize()
        members = await self._redis.client.smembers(self._user_index_key(user_id))
        return list(members or [])
