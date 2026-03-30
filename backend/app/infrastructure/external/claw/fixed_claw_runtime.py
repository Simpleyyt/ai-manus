import asyncio
import logging
from typing import Optional

import httpx

from app.domain.external.claw import ClawInstanceInfo
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class FixedClawRuntime:
    """Uses a pre-configured fixed address — no actual creation.

    Suitable for development or when the claw instance is managed
    externally (e.g., on a remote machine).
    """

    creates_immediately = True

    def __init__(self, address: str):
        self._address = address
        self.settings = get_settings()

    async def create(self, claw_id: str, api_key: str) -> ClawInstanceInfo:
        return ClawInstanceInfo(address=self._address)

    async def destroy(self, instance_name: Optional[str]) -> None:
        pass

    async def wait_for_ready(self, base_url: str) -> bool:
        timeout = self.settings.claw_ready_timeout
        interval = 2.0
        max_retries = int(timeout / interval)
        async with httpx.AsyncClient(timeout=5.0) as client:
            for _ in range(max_retries):
                try:
                    resp = await client.get(f"{base_url}/health")
                    if resp.status_code == 200:
                        logger.info(f"Fixed claw instance ready: {base_url}")
                        return True
                except Exception:
                    pass
                await asyncio.sleep(interval)
        logger.warning(f"Fixed claw instance not ready after {timeout}s: {base_url}")
        return False
