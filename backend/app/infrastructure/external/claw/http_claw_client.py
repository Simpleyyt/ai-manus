import json
import logging
from typing import List, AsyncIterator

import httpx

from app.domain.models.claw import ClawMessage, ClawAttachment

logger = logging.getLogger(__name__)


class HttpClawClient:
    """Communicates with a claw instance over its HTTP API."""

    async def chat_stream(
        self, base_url: str, message: str, session_id: str,
    ) -> AsyncIterator[dict]:
        url = f"{base_url}/chat"
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                json={"message": message, "session_id": session_id, "stream": True},
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    try:
                        yield json.loads(data)
                    except Exception:
                        continue

    async def get_history(
        self, base_url: str, session_id: str, limit: int = 200,
    ) -> List[ClawMessage]:
        url = f"{base_url}/history"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params={
                "session_id": session_id,
                "limit": str(limit),
            })
            if resp.status_code != 200:
                return []
            data = resp.json()
            import re

            messages = []
            seen_file_ids: set[str] = set()

            def _parse_attachments(raw_atts) -> list[ClawAttachment] | None:
                if not raw_atts or not isinstance(raw_atts, list):
                    return None
                parsed = []
                for a in raw_atts:
                    file_id = a.get("file_id", "")
                    if not file_id:
                        uri = a.get("uri", "")
                        match = re.search(r'manus-file://([a-f0-9]{24})', uri)
                        if match:
                            file_id = match.group(1)
                    if file_id and file_id not in seen_file_ids:
                        seen_file_ids.add(file_id)
                        parsed.append(ClawAttachment(
                            file_id=file_id,
                            filename=a.get("filename", "") or a.get("name", "") or file_id,
                            content_type=a.get("content_type") or a.get("mimeType") or None,
                            size=a.get("size", 0) or 0,
                        ))
                return parsed or None

            for m in data.get("messages", []):
                role = m.get("role", "")
                content = m.get("content", "")
                ts = int(m.get("timestamp", 0))
                attachments = _parse_attachments(m.get("attachments"))

                if role == "toolResult":
                    if attachments:
                        messages.append(ClawMessage(
                            role="assistant", content="",
                            timestamp=ts, attachments=attachments,
                        ))
                    continue

                if role not in ("user", "assistant"):
                    continue

                # Skip empty assistant messages (tool-call intermediate steps)
                if role == "assistant" and not content.strip() and not attachments:
                    continue

                messages.append(ClawMessage(
                    role=role, content=content,
                    timestamp=ts, attachments=attachments,
                ))
            return messages

    async def get_file(self, base_url: str, filename: str) -> tuple[bytes, str]:
        url = f"{base_url}/files/{filename}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "application/octet-stream")
            return response.content, content_type
