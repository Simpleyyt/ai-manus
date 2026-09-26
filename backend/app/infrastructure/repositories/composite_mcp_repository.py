from typing import Optional

from app.application.services.connector_service import ConnectorService
from app.domain.models.mcp_config import MCPConfig


class ConnectorMCPRepository:
    """MCP servers for one user: enabled Mongo connectors only."""

    def __init__(self, connector_service: ConnectorService):
        self._connector_service = connector_service

    async def get_mcp_config(self, user_id: Optional[str] = None) -> MCPConfig:
        if not user_id:
            return MCPConfig()
        return await self._connector_service.mcp_config_for_user(user_id)
