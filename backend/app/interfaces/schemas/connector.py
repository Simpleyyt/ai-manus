from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.models.mcp_config import MCPTransport


class ConnectorEnvFieldItem(BaseModel):
    key: str
    label: str
    secret: bool = True
    placeholder: Optional[str] = None


class ConnectorCatalogItemResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon_url: Optional[str] = None
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env_fields: List[ConnectorEnvFieldItem] = Field(default_factory=list)
    header_fields: List[ConnectorEnvFieldItem] = Field(default_factory=list)


class ConnectedConnectorItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    source: str
    catalog_id: Optional[str] = None
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


class ConnectorsStateResponse(BaseModel):
    catalog: List[ConnectorCatalogItemResponse]
    connected: List[ConnectedConnectorItem]


class ConnectBuiltinRequest(BaseModel):
    catalog_id: str
    env: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None


class CreateCustomConnectorRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None


class UpdateConnectorRequest(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    transport: Optional[MCPTransport] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None


class TestConnectorRequest(BaseModel):
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None


class TestConnectorResponse(BaseModel):
    success: bool
    message: str
    tools: List[str] = Field(default_factory=list)
