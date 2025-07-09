from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MCPTransport(str, Enum):
    """MCP transport types"""
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


class MCPServerConfig(BaseModel):
    """
    MCP server configuration model
    """
    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    
    # For HTTP-based transports
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    # Common fields
    transport: MCPTransport
    enabled: bool = Field(default=True)
    description: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    
    @field_validator("url")
    def validate_url_for_http_transport(cls, v: Optional[str], values) -> Optional[str]:
        """Validate URL is required for HTTP-based transports"""
        if hasattr(values, 'data'):
            transport = values.data.get('transport')
            if transport in [MCPTransport.SSE, MCPTransport.STREAMABLE_HTTP] and not v:
                raise ValueError("URL is required for HTTP-based transports")
        return v
    
    @field_validator("command")
    def validate_command_for_stdio(cls, v: Optional[str], values) -> Optional[str]:
        """Validate command is required for stdio transport"""
        if hasattr(values, 'data'):
            transport = values.data.get('transport')
            if transport == MCPTransport.STDIO and not v:
                raise ValueError("Command is required for stdio transport")
        return v
    
    class Config:
        extra = "allow"


class MCPConfig(BaseModel):
    """
    MCP configuration model containing all server configurations
    """
    mcpServers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"