import pytest

from app.application.services.connector_service import ConnectorService
from app.domain.models.connector import ConnectorSource, UserConnector
from app.domain.models.mcp_config import MCPTransport


class InMemoryConnectorRepository:
    def __init__(self):
        self._items: list[UserConnector] = []

    async def save(self, connector: UserConnector) -> None:
        for index, item in enumerate(self._items):
            if item.id == connector.id and item.user_id == connector.user_id:
                self._items[index] = connector
                return
        self._items.append(connector)

    async def find_by_user_id(self, user_id: str) -> list[UserConnector]:
        return [item for item in self._items if item.user_id == user_id]

    async def find_by_id_and_user_id(self, connector_id: str, user_id: str) -> UserConnector | None:
        for item in self._items:
            if item.id == connector_id and item.user_id == user_id:
                return item
        return None

    async def find_enabled_by_user_id(self, user_id: str) -> list[UserConnector]:
        return [item for item in self._items if item.user_id == user_id and item.enabled]

    async def delete_by_id_and_user_id(self, connector_id: str, user_id: str) -> bool:
        for index, item in enumerate(self._items):
            if item.id == connector_id and item.user_id == user_id:
                self._items.pop(index)
                return True
        return False


@pytest.fixture
def connector_service() -> ConnectorService:
    return ConnectorService(connector_repository=InMemoryConnectorRepository())


@pytest.mark.asyncio
async def test_connect_builtin_creates_connector(connector_service: ConnectorService):
    connector = await connector_service.connect_builtin(
        "user-1",
        "github",
        env={"GITHUB_TOKEN": "test-token"},
    )
    assert connector.catalog_id == "github"
    assert connector.source == ConnectorSource.BUILTIN
    assert connector.env == {"GITHUB_TOKEN": "test-token"}


@pytest.mark.asyncio
async def test_build_user_mcp_config_merges_enabled_connectors(connector_service: ConnectorService):
    await connector_service.connect_builtin("user-1", "github", env={"GITHUB_TOKEN": "test-token"})
    config = await connector_service.build_user_mcp_config("user-1")
    assert "github" in config.mcpServers
    assert config.mcpServers["github"].command == "npx"


@pytest.mark.asyncio
async def test_create_custom_requires_url_for_http_transport(connector_service: ConnectorService):
    with pytest.raises(Exception):
        await connector_service.create_custom(
            "user-1",
            name="Broken",
            transport=MCPTransport.STREAMABLE_HTTP,
        )
