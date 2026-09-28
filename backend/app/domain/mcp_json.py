"""Parse Cursor/Manus-style mcpServers JSON into connector payloads."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.domain.models.mcp_config import MCPTransport

_KEY_RE = re.compile(r"[^a-zA-Z0-9_]+")


class ParsedMcpServer:
    def __init__(
        self,
        name: str,
        transport: MCPTransport,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        note: Optional[str] = None,
    ):
        self.name = name
        self.transport = transport
        self.command = command
        self.args = args
        self.env = env
        self.url = url
        self.headers = headers
        self.note = note


class McpJsonError(ValueError):
    pass


def make_server_key(name: str) -> str:
    slug = _KEY_RE.sub("_", (name or "").strip()).strip("_").lower()
    if not slug:
        slug = "mcp"
    if slug[0].isdigit():
        slug = f"mcp_{slug}"
    return slug[:64]


def dict_from_pairs(pairs: Optional[List[Any]]) -> Optional[Dict[str, str]]:
    if not pairs:
        return None
    result: Dict[str, str] = {}
    for item in pairs:
        if isinstance(item, dict):
            key = str(item.get("key") or "").strip()
            value = item.get("value")
            if key:
                result[key] = "" if value is None else str(value)
        elif isinstance(item, (list, tuple)) and len(item) >= 1:
            key = str(item[0]).strip()
            if key:
                result[key] = "" if len(item) < 2 or item[1] is None else str(item[1])
    return result or None


def parse_mcp_servers_json(raw: str) -> List[ParsedMcpServer]:
    text = (raw or "").strip()
    if not text:
        raise McpJsonError("No MCP server configuration found.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise McpJsonError("Invalid MCP configuration format") from exc
    if not isinstance(data, dict):
        raise McpJsonError("Invalid MCP configuration format")
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        raise McpJsonError(
            "Missing mcpServers key in JSON configuration. "
            "Please ensure your JSON contains the mcpServers object."
        )
    parsed = [parse_server_entry(name, config) for name, config in servers.items()]
    if len(parsed) > 1:
        raise McpJsonError(
            "Only single MCP server configuration is allowed. Please import one server at a time."
        )
    return parsed


def parse_server_entry(name: str, config: Any) -> ParsedMcpServer:
    if not isinstance(config, dict):
        raise McpJsonError("Invalid MCP configuration format")
    display_name = str(name or "").strip() or "custom-mcp-server"
    transport = detect_transport_type(config)
    command = _optional_str(config.get("command"))
    args = _string_list(config.get("args") or config.get("arguments"))
    env = _string_dict(config.get("env") or config.get("envVariables"))
    url = _optional_str(config.get("url") or config.get("server_url") or config.get("serverUrl"))
    headers = _string_dict(config.get("headers") or config.get("customHeaders"))
    note = _optional_str(config.get("description") or config.get("note") or config.get("brief"))
    if transport == MCPTransport.STDIO and not command:
        raise McpJsonError("Command is required for stdio transport")
    if transport != MCPTransport.STDIO and not url:
        raise McpJsonError("URL is required for HTTP-based transports")
    return ParsedMcpServer(
        name=display_name,
        transport=transport,
        command=command,
        args=args,
        env=env,
        url=url,
        headers=headers,
        note=note,
    )


def detect_transport_type(config: Dict[str, Any]) -> MCPTransport:
    raw = (
        config.get("transport")
        or config.get("type")
        or config.get("transport_type")
        or config.get("transportType")
        or ""
    )
    token = str(raw).strip().lower().replace("_", "-")
    if token in {"stdio"}:
        return MCPTransport.STDIO
    if token in {"sse"}:
        return MCPTransport.SSE
    if token in {"http", "streamable-http", "streamablehttp", "streamable"}:
        return MCPTransport.STREAMABLE_HTTP
    if config.get("command"):
        return MCPTransport.STDIO
    return MCPTransport.STREAMABLE_HTTP


def parse_mcp_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        raise McpJsonError("Server URL is required")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise McpJsonError("Enter a valid MCP server URL")
    return value


def name_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip()
    return host or "custom-mcp-server"


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> Optional[List[str]]:
    if not value:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or None
    return None


def _string_dict(value: Any) -> Optional[Dict[str, str]]:
    if not value:
        return None
    if isinstance(value, dict):
        result = {
            str(key).strip(): "" if val is None else str(val)
            for key, val in value.items()
            if str(key).strip()
        }
        return result or None
    if isinstance(value, list):
        return dict_from_pairs(value)
    return None
