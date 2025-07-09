# MCP 配置

## 简介

MCP（Model Context Protocol）是一个开放的标准协议，用于在语言模型应用程序和外部数据源及工具之间提供安全的连接。在 AI Manus 中，MCP 允许 AI 助手访问和使用各种外部服务和工具，如 GitHub API、文件系统、数据库等。

## 演示

> 任务：统计一下 simpleyyt 用户的 github 仓库

![](https://raw.githubusercontent.com/Simpleyyt/picgo-image/master/mcp.mp4 ':include controls width="100%"')

## 配置说明

### MCP 配置文件

MCP 服务器的配置通过 `mcp.json` 文件进行管理，该文件包含了所有 MCP 服务器的配置信息。

#### 配置文件结构

```json
{
  "mcpServers": {
    "服务器名称": {
      "command": "命令",
      "args": ["参数列表"],
      "transport": "传输方式",
      "enabled": true/false,
      "description": "服务器描述",
      "env": {
        "环境变量名": "环境变量值"
      }
    }
  }
}
```

#### 当前配置示例

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

### Docker Compose 配置

在 `docker-compose.yml` 中配置 MCP 服务：

```yaml
...
services:
  backend:
    image: simpleyyt/manus-backend
    volumes:
      - ./mcp.json:/etc/mcp.json  # 挂载 MCP 配置文件
      - ...
    environment:
      # MCP 配置文件路径
      - MCP_CONFIG_PATH=/etc/mcp.json
...
```

## 更多资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP 服务器列表](https://github.com/modelcontextprotocol/servers)