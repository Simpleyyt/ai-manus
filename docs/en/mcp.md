# MCP Configuration

## Introduction

MCP (Model Context Protocol) is an open standard protocol for providing secure connections between language model applications and external data sources and tools. In AI Manus, MCP allows AI assistants to access and use various external services and tools, such as GitHub API, file systems, databases, and more.

## Demo

> Task: Analyze the GitHub repositories of user simpleyyt

![](https://raw.githubusercontent.com/Simpleyyt/picgo-image/master/mcp.mp4 ':include controls width="100%"')

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