"""Redis pub/sub notifier for session list WebSocket (event-driven)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, Optional

from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "session_list:"


def channel_for_user(user_id: str) -> str:
    return f"{CHANNEL_PREFIX}{user_id}"


async def publish_session_upsert(user_id: str, session_id: str) -> None:
    await _publish(user_id, {"op": "upsert", "session_id": session_id})


async def publish_session_remove(user_id: str, session_id: str) -> None:
    await _publish(user_id, {"op": "remove", "session_id": session_id})


async def _publish(user_id: str, payload: dict[str, Any]) -> None:
    try:
        redis = get_redis()
        await redis.initialize()
        await redis.client.publish(channel_for_user(user_id), json.dumps(payload))
    except Exception as e:
        logger.warning("Failed to publish session list notify for user %s: %s", user_id, e)


def parse_notify_payload(raw: str) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    op: Literal["upsert", "remove"] | None = data.get("op")
    session_id = data.get("session_id")
    if op not in ("upsert", "remove") or not session_id:
        return None
    return data
