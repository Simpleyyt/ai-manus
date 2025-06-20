# AI-Agent MCP 客户端集成

本文档介绍了 ai-agent 项目中集成的 Model Context Protocol (MCP) 客户端功能，使 AI Agent 能够发现、连接和使用外部 MCP 工具。

## 功能概览

MCP 客户端集成为 ai-agent 提供了以下能力：

- **工具发现**: 自动发现和连接配置的 MCP 服务器
- **动态工具注册**: 将 MCP 工具动态注册到 Agent 的工具系统中
- **统一调用接口**: 通过统一的接口调用内置工具和 MCP 工具
- **资源管理**: 自动管理 MCP 连接和清理资源

## 架构设计

### 核心组件

1. **MCPClientManager**: MCP 客户端管理器
   - 负责加载配置文件
   - 管理多个 MCP 服务器连接
   - 缓存工具列表和会话信息

2. **MCPTool**: MCP 工具类
   - 继承自 `BaseTool`
   - 提供 MCP 工具的统一接口
   - 支持同步和异步工具获取

3. **配置系统**: 基于 JSON 的配置管理
   - 支持多种传输类型（stdio, HTTP/SSE）
   - 灵活的服务器启用/禁用控制
   - 环境变量配置支持

## 配置说明

### MCP 服务器配置

配置文件位置：`mcp_servers/config.json`

```json
{
  "mcp_servers": {
    "fofa-mcp-server": {
      "description": "FOFA search engine MCP server for asset discovery",
      "command": "python",
      "args": ["mcp_servers/fofa_simple.py"],
      "env": {
        "FOFA_EMAIL": "your-email@example.com",
        "FOFA_KEY": "your-fofa-api-key"
      },
      "auto_connect": true,
      "enabled": true
    },
    "example-http-mcp-server": {
      "description": "Example HTTP/SSE MCP server",
      "transport": "http",
      "url": "http://localhost:8080",
      "auto_connect": false,
      "enabled": false
    }
  }
}
```

### 配置参数说明

- `description`: 服务器描述
- `transport`: 传输类型（`stdio` 或 `http`）
- `command`: 命令行工具（stdio 模式）
- `args`: 命令行参数（stdio 模式）
- `url`: 服务器 URL（HTTP 模式）
- `env`: 环境变量
- `auto_connect`: 是否自动连接
- `enabled`: 是否启用此服务器

## 使用方法

### 1. 基本使用

MCP 工具会自动集成到 Agent 的工具系统中，无需额外配置。当 Agent 运行时，会自动：

1. 加载 MCP 服务器配置
2. 连接到启用的服务器
3. 获取可用工具列表
4. 将工具注册到 Agent 中

### 2. 可用的内置 MCP 工具

Agent 提供了两个内置的 MCP 管理工具：

- `list_mcp_servers`: 列出所有 MCP 服务器及其状态
- `list_mcp_tools`: 列出所有可用的 MCP 工具

### 3. 与 AI 对话示例

```
用户: 请列出当前连接的 MCP 服务器

AI: 我来为你列出当前的 MCP 服务器状态。

[调用 list_mcp_servers 工具]

MCP 服务器列表:

- fofa-mcp-server: 已连接
  描述: FOFA search engine MCP server for asset discovery
  传输类型: stdio
  工具数量: 2

- amap-location: 已连接
  描述: Amap (高德地图) MCP server
  传输类型: http
  工具数量: 3
```

```
用户: 搜索 baidu.com 相关的网络资产信息

AI: 我使用 FOFA 搜索工具来查找 baidu.com 相关的网络资产信息。

[调用 mcp_fofa-mcp-server_fofa_search 工具，参数: {"domain": "baidu.com"}]

FOFA 搜索结果：

查询参数: domain="baidu.com"
找到结果数: 15

资产详情:
1. 主机名: www.baidu.com
   IP地址: 180.101.49.11
   端口: 80

2. 主机名: baidu.com
   IP地址: 180.101.49.12
   端口: 443

...
```

## 开发指南

### 添加新的 MCP 服务器

1. 在 `mcp_servers/config.json` 中添加服务器配置
2. 确保服务器可执行或可访问
3. 设置必要的环境变量
4. 重启 Agent 服务

### 工具命名规范

MCP 工具在 Agent 中的命名格式为：
```
mcp_{server_name}_{tool_name}
```

例如：
- `mcp_fofa-mcp-server_fofa_search`
- `mcp_amap-location_geocode`

### 扩展 MCP 支持

如需扩展 MCP 支持，可以修改以下文件：

- `app/domain/services/tools/mcp.py`: 核心 MCP 客户端逻辑
- `app/domain/services/agents/execution.py`: Agent 工具集成
- `mcp_servers/config.json`: 服务器配置

## 测试

### 运行测试脚本

```bash
cd backend
python test_mcp_integration.py
```

测试脚本会验证：
- MCP 客户端管理器初始化
- 服务器连接状态
- 工具发现和列表
- 工具调用功能

### 测试输出示例

```
============================================================
AI-Agent MCP 集成测试
============================================================
2024-01-20 10:30:00 - __main__ - INFO - 开始测试 MCP 客户端管理器...
2024-01-20 10:30:01 - __main__ - INFO - 发现 3 个 MCP 服务器:
2024-01-20 10:30:01 - __main__ - INFO -   - fofa-mcp-server: 已连接 (2 个工具)
2024-01-20 10:30:01 - __main__ - INFO -   - amap-location: 已连接 (3 个工具)
...
============================================================
测试结果汇总:
============================================================
MCP 客户端管理器: ✅ 通过
MCP 工具类: ✅ 通过
MCP 工具调用: ✅ 通过
============================================================
🎉 所有测试通过！MCP 集成功能正常工作。
```

## 故障排除

### 常见问题

1. **MCP 服务器连接失败**
   - 检查配置文件路径和格式
   - 验证环境变量设置
   - 确认服务器可执行权限

2. **工具调用失败**
   - 检查工具参数格式
   - 验证 API 密钥和权限
   - 查看服务器日志

3. **性能问题**
   - 减少自动连接的服务器数量
   - 使用工具缓存
   - 优化网络连接

### 日志配置

在 `app/infrastructure/logging.py` 中可以调整 MCP 相关的日志级别：

```python
logging.getLogger('app.domain.services.tools.mcp').setLevel(logging.DEBUG)
```

## 最佳实践

1. **配置管理**
   - 使用环境变量存储敏感信息
   - 定期检查服务器连接状态
   - 合理配置超时时间

2. **性能优化**
   - 只启用必要的 MCP 服务器
   - 使用连接池管理多个连接
   - 实现工具调用的缓存机制

3. **安全考虑**
   - 验证 MCP 服务器的可信度
   - 限制工具的执行权限
   - 定期更新 API 密钥

## 技术细节

### 支持的传输类型

- **stdio**: 标准输入输出，适用于本地 MCP 服务器
- **HTTP/SSE**: 基于 Server-Sent Events 的 HTTP 连接，适用于远程服务器

### 异步架构

MCP 集成采用完全异步的架构设计：
- 异步连接管理
- 异步工具发现
- 异步工具调用
- 异步资源清理

### 错误处理

- 连接失败时的自动重试
- 工具调用超时处理
- 资源泄露防护
- 优雅的错误降级

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进 MCP 集成功能。

### 开发环境设置

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_mcp_integration.py

# 启动开发服务器
python main.py
```

## 许可证

此 MCP 集成功能遵循项目的开源许可证。 