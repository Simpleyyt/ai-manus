# MCP Configuration

## Introduction

MCP (Model Context Protocol) is an open standard protocol for providing secure connections between language model applications and external data sources and tools. In AI Manus, MCP allows AI assistants to access and use various external services and tools, such as GitHub API, file systems, databases, and more.

In the chat composer, the **Connect apps** (cable) button opens the official-style app list (brand icons + **Connect**) plus switches for added Custom MCP servers. **Add connectors** shows overlapping logo previews and opens the browse dialog with **Apps / Custom API / Custom MCP / Projects** tabs. **Manage connectors** opens Settings → Connectors. Disabled Custom MCP servers are omitted from the agent MCP toolkit. Marketplace OAuth is not wired; **Connect** / card **Plus** only open the browse shell.

## Demo

> Task: Analyze the GitHub repositories of user simpleyyt

![](https://github.com/user-attachments/assets/1eeecd48-7c03-4ecd-ae5c-865a4a44a430 ':include controls width="100%"')

## Configuration Guide

### MCP Configuration File

MCP server configuration is managed through the `mcp.json` file, which contains configuration information for all MCP servers.

#### Configuration File Structure

```json
{
  "mcpServers": {
    "server_name": {
      "command": "command",
      "args": ["argument_list"],
      "transport": "transport_method",
      "enabled": true/false,
      "description": "server_description",
      "env": {
        "environment_variable_name": "environment_variable_value"
      }
    }
  }
}
```

#### Current Configuration Example

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "transport": "stdio",
      "enabled": true,
      "description": "GitHub API integration",
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### Docker Compose Configuration

Configure MCP service in `docker-compose.yml`:

```yaml
...
services:
  backend:
    image: simpleyyt/manus-backend
    volumes:
      - ./mcp.json:/etc/mcp.json  # Mount MCP configuration file
      - ...
    environment:
      # MCP configuration file path
      - MCP_CONFIG_PATH=/etc/mcp.json
...
```

## Additional Resources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [MCP Server List](https://github.com/modelcontextprotocol/servers) 