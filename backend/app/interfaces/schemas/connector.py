from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.models.mcp_config import MCPTransport


class VariableItem(BaseModel):
    key: str
    value: str = ""


class ConnectorItem(BaseModel):
    id: str
    name: str
    server_key: str
    note: Optional[str] = None
    icon_url: Optional[str] = None
    transport: MCPTransport
    enabled: bool = True
    source: str
    readonly: bool = False
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[List[VariableItem]] = None
    url: Optional[str] = None
    headers: Optional[List[VariableItem]] = None


class ListConnectorsResponse(BaseModel):
    connectors: List[ConnectorItem]


class ConnectorWriteRequest(BaseModel):
    name: str
    note: Optional[str] = None
    icon_url: Optional[str] = None
    transport: MCPTransport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[List[VariableItem]] = None
    url: Optional[str] = None
    headers: Optional[List[VariableItem]] = None


class ImportMcpJsonRequest(BaseModel):
    json: str = Field(min_length=1)


class CreateMcpFromUrlRequest(BaseModel):
    url: str
    name: Optional[str] = None


class ConnectorEnabledRequest(BaseModel):
    enabled: bool


def pairs_to_dict(items: Optional[List[VariableItem]]) -> Optional[Dict[str, str]]:
    if not items:
        return None
    result = {
        item.key.strip(): item.value
        for item in items
        if item.key and item.key.strip()
    }
    return result or None


def dict_to_pairs(values: Optional[Dict[str, str]]) -> Optional[List[VariableItem]]:
    if not values:
        return None
    return [VariableItem(key=key, value=value) for key, value in values.items()]
