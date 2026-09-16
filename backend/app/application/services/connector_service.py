import logging
from datetime import UTC, datetime
from typing import Dict, List, Optional, Tuple

from app.application.data.official_connectors import OFFICIAL_CONNECTOR_BY_ID, OFFICIAL_CONNECTORS
from app.application.errors.exceptions import BadRequestError, NotFoundError
from app.domain.models.connector import ConnectorCatalogItem, ConnectorSource, UserConnector
from app.domain.models.mcp_config import MCPConfig, MCPServerConfig, MCPTransport
from app.domain.repositories.connector_repository import ConnectorRepository
from app.domain.services.tools.mcp import MCPClientManager

logger = logging.getLogger(__name__)


class ConnectorService:
    def __init__(self, connector_repository: ConnectorRepository):
        self._connector_repository = connector_repository

    async def get_state(self, user_id: str) -> Tuple[List[ConnectorCatalogItem], List[UserConnector]]:
        connected = await self._connector_repository.find_by_user_id(user_id)
        return OFFICIAL_CONNECTORS, connected

    async def connect_builtin(
        self,
        user_id: str,
        catalog_id: str,
        env: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> UserConnector:
        catalog_item = OFFICIAL_CONNECTOR_BY_ID.get(catalog_id)
        if not catalog_item:
            raise NotFoundError(f"Connector not found: {catalog_id}")

        existing = next(
            (item for item in await self._connector_repository.find_by_user_id(user_id) if item.catalog_id == catalog_id),
            None,
        )
        if existing:
            existing.env = env or existing.env
            existing.headers = headers or existing.headers
            existing.enabled = True
            existing.updated_at = datetime.now(UTC)
            await self._connector_repository.save(existing)
            return existing

        connector = UserConnector(
            user_id=user_id,
            name=catalog_item.name,
            description=catalog_item.description,
            icon_url=catalog_item.icon_url,
            source=ConnectorSource.BUILTIN,
            catalog_id=catalog_id,
            transport=catalog_item.transport,
            command=catalog_item.command,
            args=catalog_item.args,
            url=catalog_item.url,
            headers=headers,
            env=env,
            enabled=True,
        )
        await self._connector_repository.save(connector)
        return connector

    async def create_custom(
        self,
        user_id: str,
        name: str,
        transport: MCPTransport,
        description: Optional[str] = None,
        icon_url: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> UserConnector:
        if not name.strip():
            raise BadRequestError("Connector name is required")
        self._validate_transport_config(transport, command=command, url=url)

        connector = UserConnector(
            user_id=user_id,
            name=name.strip(),
            description=description,
            icon_url=icon_url,
            source=ConnectorSource.CUSTOM,
            transport=transport,
            command=command,
            args=args,
            url=url,
            headers=headers,
            env=env,
            enabled=True,
        )
        await self._connector_repository.save(connector)
        return connector

    async def update_connector(
        self,
        user_id: str,
        connector_id: str,
        *,
        enabled: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        transport: Optional[MCPTransport] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> UserConnector:
        connector = await self._connector_repository.find_by_id_and_user_id(connector_id, user_id)
        if not connector:
            raise NotFoundError("Connector not found")

        if enabled is not None:
            connector.enabled = enabled
        if name is not None:
            connector.name = name.strip()
        if description is not None:
            connector.description = description
        if transport is not None:
            connector.transport = transport
        if command is not None:
            connector.command = command
        if args is not None:
            connector.args = args
        if url is not None:
            connector.url = url
        if headers is not None:
            connector.headers = headers
        if env is not None:
            connector.env = env

        self._validate_transport_config(connector.transport, command=connector.command, url=connector.url)
        connector.updated_at = datetime.now(UTC)
        await self._connector_repository.save(connector)
        return connector

    async def delete_connector(self, user_id: str, connector_id: str) -> None:
        deleted = await self._connector_repository.delete_by_id_and_user_id(connector_id, user_id)
        if not deleted:
            raise NotFoundError("Connector not found")

    async def test_connection(
        self,
        transport: MCPTransport,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str, List[str]]:
        self._validate_transport_config(transport, command=command, url=url)
        server_key = "test"
        config = MCPConfig(
            mcpServers={
                server_key: MCPServerConfig(
                    transport=transport,
                    command=command,
                    args=args,
                    url=url,
                    headers=headers,
                    env=env,
                    enabled=True,
                )
            }
        )
        manager = MCPClientManager(config)
        try:
            await manager.initialize()
            tools = await manager.get_all_tools()
            tool_names = [tool["function"]["name"] for tool in tools]
            return True, f"Connected successfully ({len(tool_names)} tools)", tool_names
        except Exception as exc:
            logger.warning("Connector test failed: %s", exc)
            return False, str(exc), []
        finally:
            await manager.cleanup()

    async def build_user_mcp_config(self, user_id: str) -> MCPConfig:
        connectors = await self._connector_repository.find_enabled_by_user_id(user_id)
        servers: Dict[str, MCPServerConfig] = {}
        for connector in connectors:
            servers[connector.to_mcp_server_key()] = MCPServerConfig(
                transport=connector.transport,
                command=connector.command,
                args=connector.args,
                url=connector.url,
                headers=connector.headers,
                env=connector.env,
                enabled=True,
                description=connector.description,
            )
        return MCPConfig(mcpServers=servers)

    @staticmethod
    def _validate_transport_config(
        transport: MCPTransport,
        *,
        command: Optional[str],
        url: Optional[str],
    ) -> None:
        if transport == MCPTransport.STDIO and not command:
            raise BadRequestError("Command is required for stdio transport")
        if transport in {MCPTransport.SSE, MCPTransport.STREAMABLE_HTTP} and not url:
            raise BadRequestError("URL is required for HTTP-based transport")
