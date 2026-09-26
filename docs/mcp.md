# MCP 配置

## 简介

MCP（Model Context Protocol）是一个开放的标准协议，用于在语言模型应用程序和外部数据源及工具之间提供安全的连接。在 AI Manus 中，MCP 允许 AI 助手访问和使用各种外部服务和工具，如 GitHub API、文件系统、数据库等。

在对话输入框左侧点击 **Connect apps**（插头）会列出已添加的 Custom MCP 开关；**Add connectors** 打开浏览对话框。**Apps** 读仓库根目录的 `connectors.json`（backend 每次请求重新读取），**Custom MCP** 管理本机添加的服务器。**Manage connectors** 进入设置中的 Connectors 页。禁用的 Custom MCP 不会进入当次 Agent 的 MCP 工具集。

`connectors.json` 里的每一条点 **Plus** 会按文件中的 URL 创建真实 Custom MCP，写入 Mongo 并进入 `MCPToolkit`。带 `headers` 的条目会先弹出表单。同一 `uid` 已安装时显示 **Check**，不会重复创建。改这个文件后重新打开 Apps 即可，不必改前端代码。

## 演示

> 任务：统计一下 simpleyyt 用户的 github 仓库

![](https://github.com/user-attachments/assets/1eeecd48-7c03-4ecd-ae5c-865a4a44a430 ':include controls width="100%"')

## 配置说明

### Apps 目录

仓库根目录的 `connectors.json` 就是 Connectors → Apps 列表。Docker Compose 会把它挂到 backend 的 `/etc/connectors.json`。未设置 `CONNECTOR_CATALOG_PATH` 时，backend 优先读这个挂载文件，否则读仓库根目录的同一份文件。

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

`transport` 只接受 `streamable-http` 或 `sse`。`order` 为 `0` 或省略时排在最后。缺 URL、传输方式不对的条目会被跳过。安装时 backend 只认 `uid`，名称和地址以文件为准。

单个 Custom MCP 在设置或 **Custom MCP** 里添加，写入 Mongo。

## 更多资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP 服务器列表](https://github.com/modelcontextprotocol/servers)