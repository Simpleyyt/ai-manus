import logging
from typing import Optional

from app.application.services.connector_service import ConnectorService
from app.domain.models.mcp_config import MCPConfig
from app.domain.repositories.mcp_repository import MCPRepository

logger = logging.getLogger(__name__)


class CompositeMCPRepository(MCPRepository):
    """Merge global file-based MCP config with per-user connectors."""

    def __init__(self, file_repository: MCPRepository, connector_service: ConnectorService):
        self._file_repository = file_repository
        self._connector_service = connector_service

    async def get_mcp_config(self, user_id: Optional[str] = None) -> MCPConfig:
        file_config = await self._file_repository.get_mcp_config()
        if not user_id or user_id == "anonymous":
            return file_config

        try:
            user_config = await self._connector_service.build_user_mcp_config(user_id)
        except Exception as exc:
            logger.exception("Failed to load user MCP connectors for %s: %s", user_id, exc)
            return file_config

        merged_servers = dict(file_config.mcpServers)
        merged_servers.update(user_config.mcpServers)
        return MCPConfig(mcpServers=merged_servers)
