from datetime import UTC, datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from app.application.errors.exceptions import BadRequestError, NotFoundError
from app.domain.mcp_json import (
    McpJsonError,
    make_server_key,
    name_from_url,
    parse_mcp_servers_json,
    parse_mcp_url,
)
from app.domain.models.connector import Connector, ConnectorSource
from app.domain.models.connector_catalog import CatalogConnector
from app.domain.models.mcp_config import MCPConfig, MCPServerConfig, MCPTransport
from app.domain.repositories.connector_catalog_repository import ConnectorCatalogRepository
from app.domain.repositories.connector_repository import ConnectorRepository
from app.domain.repositories.mcp_repository import MCPRepository


class _EmptyConnectorCatalog:
    def list_entries(self) -> List[CatalogConnector]:
        return []

    def get(self, uid: str) -> Optional[CatalogConnector]:
        return None


class ConnectorService:
    def __init__(
        self,
        connector_repository: ConnectorRepository,
        file_mcp_repository: MCPRepository,
        catalog: Optional[ConnectorCatalogRepository] = None,
    ):
        self._connectors = connector_repository
        self._file_mcp = file_mcp_repository
        self._catalog = catalog or _EmptyConnectorCatalog()

    async def list_connectors(self, user_id: str) -> List[Connector]:
        user_connectors = await self._connectors.find_by_user_id(user_id)
        file_connectors = await self._file_connectors()
        return [*user_connectors, *file_connectors]

    async def create_connector(
        self,
        user_id: str,
        *,
        name: str,
        transport: MCPTransport,
        source: ConnectorSource = ConnectorSource.FORM,
        note: Optional[str] = None,
        icon_url: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        catalog_uid: Optional[str] = None,
    ) -> Connector:
        connector = Connector(
            user_id=user_id,
            name=_require_name(name),
            server_key="",
            note=_optional_text(note),
            icon_url=_optional_text(icon_url),
            catalog_uid=_optional_text(catalog_uid),
            transport=transport,
            source=source,
            command=_optional_text(command),
            args=_clean_list(args),
            env=_clean_dict(env),
            url=_optional_text(url),
            headers=_clean_dict(headers),
        )
        _validate_transport_fields(connector)
        await self._ensure_unique_name(user_id, connector.name)
        connector.server_key = await self._unique_server_key(user_id, connector.name)
        await self._connectors.save(connector)
        return connector

    async def update_connector(
        self,
        user_id: str,
        connector_id: str,
        *,
        name: str,
        transport: MCPTransport,
        note: Optional[str] = None,
        icon_url: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Connector:
        connector = await self._require_user_connector(user_id, connector_id)
        connector.name = _require_name(name)
        connector.note = _optional_text(note)
        connector.icon_url = _optional_text(icon_url)
        connector.transport = transport
        connector.command = _optional_text(command)
        connector.args = _clean_list(args)
        connector.env = _clean_dict(env)
        connector.url = _optional_text(url)
        connector.headers = _clean_dict(headers)
        connector.updated_at = datetime.now(UTC)
        _validate_transport_fields(connector)
        await self._ensure_unique_name(user_id, connector.name, exclude_id=connector.id)
        await self._connectors.save(connector)
        return connector

    async def delete_connector(self, user_id: str, connector_id: str) -> None:
        connector = await self._require_user_connector(user_id, connector_id)
        deleted = await self._connectors.delete(connector.id, user_id)
        if not deleted:
            raise NotFoundError("Connector not found")

    async def set_enabled(
        self,
        user_id: str,
        connector_id: str,
        enabled: bool,
    ) -> Connector:
        connector = await self._require_user_connector(user_id, connector_id)
        connector.enabled = bool(enabled)
        connector.updated_at = datetime.now(UTC)
        await self._connectors.save(connector)
        return connector

    async def import_json(self, user_id: str, raw_json: str) -> Connector:
        try:
            parsed = parse_mcp_servers_json(raw_json)
        except McpJsonError as exc:
            raise BadRequestError(str(exc)) from exc
        server = parsed[0]
        return await self.create_connector(
            user_id,
            name=server.name,
            transport=server.transport,
            source=ConnectorSource.JSON,
            note=server.note,
            command=server.command,
            args=server.args,
            env=server.env,
            url=server.url,
            headers=server.headers,
        )

    async def create_from_url(
        self,
        user_id: str,
        url: str,
        name: Optional[str] = None,
    ) -> Connector:
        try:
            server_url = parse_mcp_url(url)
        except McpJsonError as exc:
            raise BadRequestError(str(exc)) from exc
        display_name = _optional_text(name) or name_from_url(server_url)
        transport = (
            MCPTransport.SSE
            if urlparse(server_url).path.rstrip("/").endswith("/sse")
            else MCPTransport.STREAMABLE_HTTP
        )
        return await self.create_connector(
            user_id,
            name=display_name,
            transport=transport,
            source=ConnectorSource.URL,
            url=server_url,
        )

    def list_catalog(self) -> List[CatalogConnector]:
        return self._catalog.list_entries()

    async def create_from_catalog(
        self,
        user_id: str,
        *,
        catalog_uid: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Connector:
        uid = _optional_text(catalog_uid)
        if not uid:
            raise BadRequestError("Catalog connector id is required")
        existing = await self._connectors.find_by_user_id_and_catalog_uid(user_id, uid)
        if existing:
            return existing
        entry = self._catalog.get(uid)
        if entry is None:
            raise BadRequestError("Catalog connector not found")
        transport = MCPTransport(entry.transport)
        cleaned = _clean_dict(headers) or {}
        missing = [
            field.label or field.key
            for field in entry.headers
            if not str(cleaned.get(field.key) or "").strip()
        ]
        if missing:
            raise BadRequestError("Missing required header: " + ", ".join(missing))
        display_name = await self._unique_display_name(user_id, entry.name)
        return await self.create_connector(
            user_id,
            name=display_name,
            transport=transport,
            source=ConnectorSource.CATALOG,
            note=entry.description or None,
            icon_url=entry.icon,
            url=entry.url,
            headers=cleaned or None,
            catalog_uid=uid,
        )

    async def mcp_config_for_user(self, user_id: str) -> MCPConfig:
        connectors = await self._connectors.find_by_user_id(user_id)
        servers: Dict[str, MCPServerConfig] = {}
        for connector in connectors:
            if not connector.enabled:
                continue
            servers[connector.server_key] = _to_server_config(connector)
        return MCPConfig(mcpServers=servers)

    async def _file_connectors(self) -> List[Connector]:
        config = await self._file_mcp.get_mcp_config()
        items: List[Connector] = []
        for name, server in (config.mcpServers or {}).items():
            items.append(
                Connector(
                    id=f"file:{name}",
                    user_id="",
                    name=name,
                    server_key=name,
                    note=server.description,
                    transport=server.transport,
                    enabled=server.enabled,
                    source=ConnectorSource.FILE,
                    readonly=True,
                    command=server.command,
                    args=server.args,
                    env=server.env,
                    url=server.url,
                    headers=server.headers,
                )
            )
        return items

    async def _require_user_connector(self, user_id: str, connector_id: str) -> Connector:
        if connector_id.startswith("file:"):
            raise BadRequestError("File-based MCP servers are managed in mcp.json")
        connector = await self._connectors.find_by_id_and_user_id(connector_id, user_id)
        if not connector:
            raise NotFoundError("Connector not found")
        return connector

    async def _ensure_unique_name(
        self,
        user_id: str,
        name: str,
        exclude_id: Optional[str] = None,
    ) -> None:
        existing = await self._connectors.find_by_user_id_and_name(user_id, name)
        if existing and existing.id != exclude_id:
            raise BadRequestError(
                "A connector with this name already exists. Please choose a different name."
            )

    async def _unique_display_name(self, user_id: str, name: str) -> str:
        existing = await self._connectors.find_by_user_id_and_name(user_id, name)
        if not existing:
            return name
        suffix = 2
        while True:
            candidate = f"{name} ({suffix})"
            if len(candidate) > 80:
                candidate = f"{name[:74]} ({suffix})"
            taken = await self._connectors.find_by_user_id_and_name(user_id, candidate)
            if not taken:
                return candidate
            suffix += 1

    async def _unique_server_key(self, user_id: str, name: str) -> str:
        base = make_server_key(name)
        existing = {
            item.server_key for item in await self._connectors.find_by_user_id(user_id)
        }
        if base not in existing:
            return base
        suffix = 2
        while f"{base}_{suffix}" in existing:
            suffix += 1
        return f"{base}_{suffix}"


def _to_server_config(connector: Connector) -> MCPServerConfig:
    return MCPServerConfig(
        transport=connector.transport,
        enabled=connector.enabled,
        description=connector.note,
        command=connector.command,
        args=connector.args,
        env=connector.env,
        url=connector.url,
        headers=connector.headers,
    )


def _require_name(name: Optional[str]) -> str:
    value = (name or "").strip()
    if not value:
        raise BadRequestError("Server Name is required")
    if len(value) > 80:
        raise BadRequestError("Server Name is too long")
    return value


def _optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_list(values: Optional[List[str]]) -> Optional[List[str]]:
    if not values:
        return None
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    return cleaned or None


def _clean_dict(values: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    if not values:
        return None
    cleaned = {
        str(key).strip(): "" if val is None else str(val)
        for key, val in values.items()
        if str(key).strip()
    }
    return cleaned or None


def _validate_transport_fields(connector: Connector) -> None:
    if connector.transport == MCPTransport.STDIO:
        if not connector.command:
            raise BadRequestError("Command is required for stdio transport")
        connector.url = None
        connector.headers = None
        return
    if not connector.url:
        raise BadRequestError("URL is required for HTTP-based transports")
    try:
        parse_mcp_url(connector.url)
    except McpJsonError as exc:
        raise BadRequestError(str(exc)) from exc
    connector.command = None
    connector.args = None
    connector.env = None
