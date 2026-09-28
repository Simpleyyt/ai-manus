from datetime import UTC, datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.domain.models.mcp_config import MCPTransport


class ConnectorSource(str, Enum):
    FORM = "form"
    JSON = "json"
    URL = "url"
    CATALOG = "catalog"


class Connector(BaseModel):
    """A user-managed MCP connector (official Connectors → Custom MCP)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str
    name: str
    server_key: str
    note: Optional[str] = None
    icon_url: Optional[str] = None
    catalog_uid: Optional[str] = None
    transport: MCPTransport
    enabled: bool = True
    source: ConnectorSource = ConnectorSource.FORM
    readonly: bool = False
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
