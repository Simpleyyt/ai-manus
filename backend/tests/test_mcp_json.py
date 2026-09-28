import pytest

from app.domain.mcp_json import (
    McpJsonError,
    detect_transport_type,
    make_server_key,
    parse_mcp_servers_json,
    parse_mcp_url,
)
from app.domain.models.mcp_config import MCPTransport


def test_make_server_key_slugifies_name():
    assert make_server_key("Docs MCP") == "docs_mcp"
    assert make_server_key("123") == "mcp_123"
    assert make_server_key("  ") == "mcp"


def test_detect_transport_prefers_command_for_stdio():
    assert detect_transport_type({"command": "npx"}) == MCPTransport.STDIO
    assert detect_transport_type({"type": "sse", "url": "http://localhost"}) == MCPTransport.SSE
    assert detect_transport_type({"type": "streamableHttp", "url": "http://x"}) == MCPTransport.STREAMABLE_HTTP
    assert detect_transport_type({"transport": "stdio"}) == MCPTransport.STDIO


def test_parse_stdio_example():
    parsed = parse_mcp_servers_json(
        """
        {
          "mcpServers": {
            "stdio-server-example": {
              "command": "npx",
              "args": ["-y", "mcp-server-example"]
            }
          }
        }
        """
    )
    assert len(parsed) == 1
    assert parsed[0].transport == MCPTransport.STDIO
    assert parsed[0].command == "npx"
    assert parsed[0].args == ["-y", "mcp-server-example"]


def test_parse_missing_mcp_servers():
    with pytest.raises(McpJsonError, match="mcpServers"):
        parse_mcp_servers_json("{}")


def test_parse_mcp_url_requires_http():
    with pytest.raises(McpJsonError):
        parse_mcp_url("ftp://example.com")
    assert parse_mcp_url("https://mcp.example.com/mcp") == "https://mcp.example.com/mcp"
