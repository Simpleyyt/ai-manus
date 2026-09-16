from datetime import UTC, datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.domain.models.mcp_config import MCPTransport


class ConnectorSource(str, Enum):
    BUILTIN = "builtin"
    CUSTOM = "custom"


class ConnectorEnvField(BaseModel):
    key: str
    label: str
    secret: bool = True
    placeholder: Optional[str] = None


class ConnectorCatalogItem(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon_url: Optional[str] = None
    transport: MCPTransport = MCPTransport.STDIO
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env_fields: List[ConnectorEnvField] = Field(default_factory=list)
    header_fields: List[ConnectorEnvField] = Field(default_factory=list)


class UserConnector(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    source: ConnectorSource
    catalog_id: Optional[str] = None
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_mcp_server_key(self) -> str:
        if self.catalog_id:
            return self.catalog_id
        return f"custom_{self.id}"
