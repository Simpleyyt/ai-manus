import asyncio
import logging
from typing import Optional

import httpx

from app.domain.external.claw import ClawInstanceInfo
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DockerClawRuntime:
    """Creates claw instances as local Docker containers."""

    creates_immediately = False

    def __init__(self):
        self.settings = get_settings()

    async def create(self, claw_id: str, api_key: str) -> ClawInstanceInfo:
        import docker
        docker_client = docker.from_env()

        sandbox_network = self.settings.sandbox_network
        manus_api_base_url = self.settings.manus_api_base_url
        container_name = f"{self.settings.claw_name_prefix}-{claw_id[:8]}"

        container_config = {
            "image": self.settings.claw_image,
            "name": container_name,
            "detach": True,
            "remove": True,
            "environment": {
                "CLAW_TTL_SECONDS": str(self.settings.claw_ttl_seconds),
                "MANUS_API_KEY": api_key,
                "MANUS_API_BASE_URL": manus_api_base_url,
            },
        }
        if sandbox_network:
            container_config["network"] = sandbox_network

        container = docker_client.containers.run(**container_config)
        container.reload()

        network_settings = container.attrs["NetworkSettings"]
        ip_address = network_settings.get("IPAddress", "")
        if not ip_address and "Networks" in network_settings:
            for _, nc in network_settings["Networks"].items():
                if nc.get("IPAddress"):
                    ip_address = nc["IPAddress"]
                    break

        logger.info(f"Claw container started: {container_name} ip={ip_address}")
        return ClawInstanceInfo(address=ip_address, instance_name=container_name)

    async def destroy(self, instance_name: Optional[str]) -> None:
        if not instance_name:
            return
        try:
            import docker
            docker_client = docker.from_env()
            container = docker_client.containers.get(instance_name)
            container.remove(force=True)
        except Exception as e:
            logger.warning(f"Failed to remove container {instance_name}: {e}")

    async def wait_for_ready(
        self, base_url: str, max_retries: int = 30, interval: float = 2.0,
    ) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for _ in range(max_retries):
                try:
                    resp = await client.get(f"{base_url}/health")
                    if resp.status_code == 200:
                        logger.info(f"Claw instance ready: {base_url}")
                        return True
                except Exception:
                    pass
                await asyncio.sleep(interval)
        logger.warning(
            f"Claw instance did not become ready after {max_retries} attempts: {base_url}"
        )
        return False
