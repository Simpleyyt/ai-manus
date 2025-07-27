import os
import logging
from app.domain.repositories.mcp_repository import MCPRepository
from app.domain.models.mcp_config import MCPConfig
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class FileMCPRepository(MCPRepository):
    """Repository for MCP config stored in a file"""
    
    async def get_mcp_config(self) -> MCPConfig:
        """Get the MCP config from the file"""
        file_path = get_settings().mcp_config_path
        if not os.path.exists(file_path):
            return MCPConfig(mcpServers={})
        try:
            with open(file_path, "r") as file:
                return MCPConfig.model_validate_json(file.read())
        except Exception as e:
            logger.exception(f"Error reading MCP config file: {e}")
        
        return MCPConfig(mcpServers={})