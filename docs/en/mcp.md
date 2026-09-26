# MCP Configuration

## Introduction

MCP (Model Context Protocol) is an open standard protocol for providing secure connections between language model applications and external data sources and tools. In AI Manus, MCP allows AI assistants to access and use various external services and tools, such as GitHub API, file systems, databases, and more.

In the chat composer, the **Connect apps** (cable) button lists switches for added Custom MCP servers. **Add connectors** opens the browse dialog. **Apps** reads `connectors.json` at the repo root (the backend reloads it on each request), and **Custom MCP** manages locally added servers. **Manage connectors** opens Settings → Connectors. Disabled Custom MCP servers are omitted from the agent MCP toolkit.

Each entry in `connectors.json` creates a real Custom MCP from the URL in that file: Plus writes Mongo and feeds `MCPToolkit`. Entries with `headers` open a form first. The same `uid` shows **Check** and is not created twice. Edit the file and reopen Apps; no frontend change is required.

## Demo

> Task: Analyze the GitHub repositories of user simpleyyt

![](https://github.com/user-attachments/assets/1eeecd48-7c03-4ecd-ae5c-865a4a44a430 ':include controls width="100%"')

## Configuration Guide

### Apps catalog

`connectors.json` at the repo root is the Connectors → Apps list. Docker Compose mounts it into the backend at `/etc/connectors.json`. When `CONNECTOR_CATALOG_PATH` is unset, the backend reads that mount if it exists, otherwise the same file at the repo root.

```json
{
  "connectors": [
    {
      "uid": "learn",
      "name": "Microsoft Learn",
      "description": "Search Microsoft docs",
      "url": "https://learn.microsoft.com/api/mcp",
      "transport": "streamable-http",
      "icon": "https://example.com/learn.png",
      "order": 10
    },
    {
      "uid": "tomtom",
      "name": "TomTom Maps",
      "description": "Maps and places",
      "url": "https://mcp.tomtom.com/maps",
      "transport": "streamable-http",
      "order": 20,
      "headers": [
        { "key": "tomtom-api-key", "label": "API Key", "placeholder": "YOUR_TOMTOM_API_KEY" }
      ]
    }
  ]
}
```

`transport` must be `streamable-http` or `sse`. `order` of `0` or omitted sorts last. Rows without a URL or with another transport are skipped. Install looks up `uid` only; the name and URL come from the file.

A single Custom MCP is added in Settings or on the **Custom MCP** tab and stored in Mongo.

## Additional Resources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [MCP Server List](https://github.com/modelcontextprotocol/servers) 