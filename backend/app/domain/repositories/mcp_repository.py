from typing import Optional, Protocol
from app.domain.models.mcp_config import MCPConfig

class MCPRepository(Protocol):
    """Repository interface for MCP aggregate"""
    
    async def get_mcp_config(self, user_id: Optional[str] = None) -> MCPConfig:
        """Get the MCP config for a user (file + user connectors)."""
        ...