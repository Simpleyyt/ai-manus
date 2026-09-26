from app.application.errors.exceptions import BadRequestError, NotFoundError
from app.application.services.connector_service import ConnectorService
from app.domain.models.connector import ConnectorSource
from app.domain.models.connector_catalog import CatalogConnector, CatalogHeaderField
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

    async def find_by_user_id_and_catalog_uid(self, user_id, catalog_uid):
        if not catalog_uid:
            return None
        for item in self.items:
            if item.user_id == user_id and item.catalog_uid == catalog_uid:
                return item
        return None


class _FakeFileMcpRepository:
    def __init__(self, servers=None):
        self._config = MCPConfig(mcpServers=servers or {})

    async def get_mcp_config(self, user_id=None):
        return self._config


class _FakeCatalog:
    def __init__(self, entries=None):
        self.entries = list(entries or [])

    def list_entries(self):
        return list(self.entries)

    def get(self, uid):
        for entry in self.entries:
            if entry.uid == uid:
                return entry
        return None


def _learn_entry() -> CatalogConnector:
    return CatalogConnector(
        uid="f4c2516f-40c3-4be2-b1c6-fb18da6a04bf",
        name="Microsoft Learn",
        description="Search Microsoft docs",
        icon="https://cdn.example.com/learn.webp",
        url="https://learn.microsoft.com/api/mcp",
        transport="streamable-http",
    )


def _tomtom_entry() -> CatalogConnector:
    return CatalogConnector(
        uid="15027330-caa8-49d2-8c90-75397e2c6410",
        name="TomTom Maps",
        url="https://mcp.tomtom.com/maps",
        transport="streamable-http",
        headers=[CatalogHeaderField(key="tomtom-api-key", label="API Key")],
    )


def _service(file_servers=None, catalog=None) -> ConnectorService:
    return ConnectorService(
        _FakeConnectorRepository(),
        _FakeFileMcpRepository(file_servers),
        catalog=catalog if catalog is not None else _FakeCatalog(),
    )


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


async def test_set_enabled_excludes_connector_from_mcp_config():
    service = _service()
    created = await service.create_connector(
        "user-1",
        name="Docs MCP",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.example.com/mcp",
    )
    assert created.enabled is True
    config = await service.mcp_config_for_user("user-1")
    assert "docs_mcp" in config.mcpServers

    disabled = await service.set_enabled("user-1", created.id, False)
    assert disabled.enabled is False
    config = await service.mcp_config_for_user("user-1")
    assert "docs_mcp" not in config.mcpServers

    enabled = await service.set_enabled("user-1", created.id, True)
    assert enabled.enabled is True
    config = await service.mcp_config_for_user("user-1")
    assert "docs_mcp" in config.mcpServers


async def test_cannot_toggle_file_connector_enabled():
    service = _service({
        "github": MCPServerConfig(transport=MCPTransport.STDIO, command="npx")
    })
    try:
        await service.set_enabled("user-1", "file:github", False)
    except BadRequestError:
        pass
    else:
        raise AssertionError("expected BadRequestError")


async def test_missing_connector_raises_not_found():
    service = _service()
    try:
        await service.delete_connector("user-1", "missing")
    except NotFoundError:
        pass
    else:
        raise AssertionError("expected NotFoundError")


async def test_create_from_catalog_is_idempotent_and_feeds_mcp_config():
    entry = _learn_entry()
    service = _service(catalog=_FakeCatalog([entry]))
    created = await service.create_from_catalog("user-1", catalog_uid=entry.uid)
    assert created.source == ConnectorSource.CATALOG
    assert created.catalog_uid == entry.uid
    assert created.name == "Microsoft Learn"
    assert created.url == entry.url
    assert created.icon_url == entry.icon
    assert created.server_key == "microsoft_learn"
    again = await service.create_from_catalog("user-1", catalog_uid=entry.uid)
    assert again.id == created.id
    config = await service.mcp_config_for_user("user-1")
    assert config.mcpServers["microsoft_learn"].url == entry.url


async def test_create_from_catalog_renames_on_name_clash_and_keeps_headers():
    entry = _tomtom_entry()
    service = _service(catalog=_FakeCatalog([entry]))
    await service.create_connector(
        "user-1",
        name="TomTom Maps",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://example.com/other",
    )
    created = await service.create_from_catalog(
        "user-1",
        catalog_uid=entry.uid,
        headers={"tomtom-api-key": "secret"},
    )
    assert created.name == "TomTom Maps (2)"
    assert created.url == entry.url
    assert created.headers["tomtom-api-key"] == "secret"
    config = await service.mcp_config_for_user("user-1")
    assert config.mcpServers[created.server_key].headers["tomtom-api-key"] == "secret"


async def test_create_from_catalog_requires_known_uid_and_headers():
    entry = _tomtom_entry()
    service = _service(catalog=_FakeCatalog([entry]))
    try:
        await service.create_from_catalog("user-1", catalog_uid="  ")
    except BadRequestError as exc:
        assert "Catalog connector id" in exc.msg
    else:
        raise AssertionError("expected BadRequestError")
    try:
        await service.create_from_catalog("user-1", catalog_uid="missing")
    except BadRequestError as exc:
        assert "not found" in exc.msg
    else:
        raise AssertionError("expected BadRequestError")
    try:
        await service.create_from_catalog("user-1", catalog_uid=entry.uid)
    except BadRequestError as exc:
        assert "tomtom-api-key" in exc.msg or "API Key" in exc.msg
    else:
        raise AssertionError("expected BadRequestError")


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
