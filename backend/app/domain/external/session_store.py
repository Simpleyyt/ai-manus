"""Protocol for opaque server-side auth sessions (Redis-backed)."""

from __future__ import annotations

from typing import Optional, Protocol

from app.domain.models.auth_session import AuthSession


class SessionStore(Protocol):
    """Store and index auth sessions for revoke / sliding TTL."""

    async def create(self, session: AuthSession, ttl_seconds: int) -> None:
        """Persist a new session and index it under the user."""
        ...

    async def get(self, session_id: str) -> Optional[AuthSession]:
        """Load a session by opaque id, or None if missing/expired."""
        ...

    async def touch(self, session_id: str, ttl_seconds: int) -> Optional[AuthSession]:
        """Sliding renewal: refresh last_seen_at / expires_at and Redis TTL."""
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete one session and remove it from the user index."""
        ...

    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete every session for a user. Returns count removed."""
        ...

    async def list_ids_for_user(self, user_id: str) -> list[str]:
        """Return session ids currently indexed for a user."""
        ...
