from typing import Optional

from app.application.services.connector_service import ConnectorService
from app.domain.models.mcp_config import MCPConfig
from app.domain.repositories.mcp_repository import MCPRepository


class CompositeMCPRepository:
    """Merge host mcp.json with the current user's enabled connectors.

    Implements MCPRepository structurally: get_mcp_config(user_id) returns
    file servers plus that user's Mongo connectors (user keys win on clash).
    """

    def __init__(self, file_repository: MCPRepository, connector_service: ConnectorService):
        self._file_repository = file_repository
        self._connector_service = connector_service

    async def get_mcp_config(self, user_id: Optional[str] = None) -> MCPConfig:
        file_config = await self._file_repository.get_mcp_config()
        if not user_id:
            return file_config
        user_config = await self._connector_service.mcp_config_for_user(user_id)
        merged = dict(file_config.mcpServers)
        merged.update(user_config.mcpServers)
        return MCPConfig(mcpServers=merged)
