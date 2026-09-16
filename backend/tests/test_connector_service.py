from app.application.errors.exceptions import BadRequestError, NotFoundError
from app.application.services.connector_service import ConnectorService
from app.domain.models.connector import ConnectorSource
from app.domain.models.mcp_config import MCPConfig, MCPServerConfig, MCPTransport
from app.infrastructure.repositories.composite_mcp_repository import CompositeMCPRepository


class _FakeConnectorRepository:
    def __init__(self):
        self.items = []

    async def save(self, connector):
        self.items = [item for item in self.items if item.id != connector.id]
        self.items.append(connector)

    async def delete(self, connector_id, user_id):
        before = len(self.items)
        self.items = [
            item for item in self.items
            if not (item.id == connector_id and item.user_id == user_id)
        ]
        return len(self.items) < before

    async def find_by_user_id(self, user_id):
        return [item for item in self.items if item.user_id == user_id]

    async def find_by_id_and_user_id(self, connector_id, user_id):
        for item in self.items:
            if item.id == connector_id and item.user_id == user_id:
                return item
        return None

    async def find_by_user_id_and_name(self, user_id, name):
        for item in self.items:
            if item.user_id == user_id and item.name == name:
                return item
        return None


class _FakeFileMcpRepository:
    def __init__(self, servers=None):
        self._config = MCPConfig(mcpServers=servers or {})

    async def get_mcp_config(self, user_id=None):
        return self._config


def _service(file_servers=None) -> ConnectorService:
    return ConnectorService(_FakeConnectorRepository(), _FakeFileMcpRepository(file_servers))


async def test_create_http_connector_and_merge_into_mcp_config():
    service = _service({
        "github": MCPServerConfig(
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            enabled=True,
        )
    })

    created = await service.create_connector(
        "user-1",
        name="Docs MCP",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.example.com/mcp",
        headers={"Authorization": "Bearer token"},
    )

    assert created.server_key == "docs_mcp"
    assert created.source == ConnectorSource.FORM
    listed = await service.list_connectors("user-1")
    assert [item.name for item in listed] == ["Docs MCP", "github"]
    assert listed[1].readonly is True

    config = await service.mcp_config_for_user("user-1")
    assert "docs_mcp" in config.mcpServers
    assert config.mcpServers["docs_mcp"].url == "https://mcp.example.com/mcp"
    assert config.mcpServers["docs_mcp"].transport == MCPTransport.STREAMABLE_HTTP


async def test_import_json_accepts_official_streamable_http_shape():
    service = _service()
    created = await service.import_json(
        "user-1",
        """
        {
          "mcpServers": {
            "http-server-example": {
              "type": "streamableHttp",
              "url": "http://localhost:3001",
              "headers": {
                "Authorization": "Bearer your-token"
              }
            }
          }
        }
        """,
    )
    assert created.name == "http-server-example"
    assert created.source == ConnectorSource.JSON
    assert created.transport == MCPTransport.STREAMABLE_HTTP
    assert created.url == "http://localhost:3001"
    assert created.headers["Authorization"] == "Bearer your-token"


async def test_import_json_rejects_multiple_servers():
    service = _service()
    try:
        await service.import_json(
            "user-1",
            '{"mcpServers":{"a":{"command":"npx"},"b":{"command":"npx"}}}',
        )
    except BadRequestError as exc:
        assert "one server" in exc.msg
    else:
        raise AssertionError("expected BadRequestError")


async def test_create_from_url_detects_sse_path():
    service = _service()
    created = await service.create_from_url("user-1", "https://mcp.example.com/sse")
    assert created.source == ConnectorSource.URL
    assert created.transport == MCPTransport.SSE
    assert created.name == "mcp.example.com"


async def test_create_from_url_defaults_to_streamable_http():
    service = _service()
    created = await service.create_from_url("user-1", "https://mcp.example.com/mcp")
    assert created.transport == MCPTransport.STREAMABLE_HTTP
    assert created.url == "https://mcp.example.com/mcp"


async def test_duplicate_name_is_rejected():
    service = _service()
    await service.create_connector(
        "user-1",
        name="GitHub",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    )
    try:
        await service.create_connector(
            "user-1",
            name="GitHub",
            transport=MCPTransport.STDIO,
            command="npx",
        )
    except BadRequestError as exc:
        assert "already exists" in exc.msg
    else:
        raise AssertionError("expected BadRequestError")


async def test_cannot_delete_file_connector():
    service = _service({
        "github": MCPServerConfig(transport=MCPTransport.STDIO, command="npx")
    })
    try:
        await service.delete_connector("user-1", "file:github")
    except BadRequestError:
        pass
    else:
        raise AssertionError("expected BadRequestError")


async def test_update_and_delete_user_connector():
    service = _service()
    created = await service.create_connector(
        "user-1",
        name="Local",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "mcp-server-example"],
    )
    updated = await service.update_connector(
        "user-1",
        created.id,
        name="Local SSE",
        transport=MCPTransport.SSE,
        url="http://localhost:3000",
    )
    assert updated.name == "Local SSE"
    assert updated.command is None
    await service.delete_connector("user-1", created.id)
    assert await service.list_connectors("user-1") == []


async def test_missing_connector_raises_not_found():
    service = _service()
    try:
        await service.delete_connector("user-1", "missing")
    except NotFoundError:
        pass
    else:
        raise AssertionError("expected NotFoundError")


async def test_composite_mcp_repository_merges_user_over_file():
    class FileRepo:
        async def get_mcp_config(self, user_id=None):
            return MCPConfig(mcpServers={
                "github": MCPServerConfig(transport=MCPTransport.STDIO, command="npx"),
            })

    class Service:
        async def mcp_config_for_user(self, user_id):
            assert user_id == "user-1"
            return MCPConfig(mcpServers={
                "docs_mcp": MCPServerConfig(
                    transport=MCPTransport.STREAMABLE_HTTP,
                    url="https://mcp.example.com/mcp",
                ),
            })

    repo = CompositeMCPRepository(FileRepo(), Service())
    config = await repo.get_mcp_config("user-1")
    assert set(config.mcpServers) == {"github", "docs_mcp"}
