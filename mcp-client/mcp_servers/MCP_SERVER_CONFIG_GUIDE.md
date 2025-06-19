###### 重要 ######
第一步： cp config.json.example config.json

第二部： 在config.json里添加你的 mcp server json


# MCP服务器配置指南

## 概述

本文档详细说明了`ai-manus-5`中MCP (Model Context Protocol) 服务器的配置文件`config.json`的字段含义、配置方法和最佳实践。

## 配置文件位置

- **容器路径**: `/mcp_servers/config.json`
- **开发环境**: `ai-manus-5/mcp-client/mcp_servers/config.json`
- **相对路径**: `mcp_servers/config.json`

## 配置文件结构

### 顶级结构

```json
{
  "preset_servers": {
    "server-id-1": { /* 服务器配置 */ },
    "server-id-2": { /* 服务器配置 */ }
  }
}
```

**字段说明:**
- `preset_servers`: **对象** - 预设MCP服务器的配置容器，包含所有可用的MCP服务器定义

## 服务器配置字段详解

### 基础字段

#### `description` (可选)
- **类型**: `string`
- **默认值**: `"MCP Server: {server_id}"`
- **说明**: 服务器的描述信息，用于UI显示和日志记录
- **示例**: `"FOFA search engine MCP server for asset discovery"`

#### `enabled` (可选)
- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用此服务器，设为`false`时不会尝试连接
- **示例**: `true`

#### `auto_connect` (可选)
- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否在系统启动时自动连接此服务器
- **示例**: `true`

### 传输方式配置

#### `transport` (可选)
- **类型**: `string`
- **枚举值**: `"stdio"` | `"http"`
- **默认值**: `"stdio"` (如果有command字段) 或 `"http"` (如果有url字段)
- **说明**: 与MCP服务器的通信方式
  - `stdio`: 通过标准输入输出与本地进程通信
  - `http`: 通过HTTP/SSE与远程服务通信

#### `protocol` (HTTP传输时可选)
- **类型**: `string`
- **枚举值**: `"rest"` | `"sse"`
- **默认值**: `"rest"` (普通HTTP API) 或 `"sse"` (如果URL中包含"/sse")
- **说明**: HTTP传输的具体协议类型
  - `rest`: 标准HTTP REST API，使用JSON请求/响应
  - `sse`: Server-Sent Events流式协议，用于实时数据传输
- **自动检测**: 系统会根据URL自动检测协议类型
  - 如果URL包含`/sse`或`sse?`，自动设置为`"sse"`
  - 否则默认为`"rest"`

### STDIO传输配置

#### `command` (stdio必需)
- **类型**: `string`
- **说明**: 启动MCP服务器的命令
- **示例**: `"python"`, `"node"`, `"./server"`

#### `args` (stdio必需)
- **类型**: `array<string>`
- **说明**: 传递给命令的参数列表
- **示例**: `["/mcp_servers/fofa.py"]`, `["-m", "mcp_server_zoomeye"]`

#### `env` (stdio可选)
- **类型**: `object<string, string>`
- **说明**: 服务器进程的环境变量
- **支持功能**:
  - 环境变量替换: `${VAR_NAME}`
  - 默认值语法: `${VAR_NAME:-default_value}`
- **示例**:
```json
{
  "FOFA_EMAIL": "${FOFA_EMAIL:-your_email@example.com}",
  "FOFA_KEY": "${FOFA_KEY}",
  "PYTHONPATH": "/app"
}
```

### HTTP传输配置

#### `url` (http必需)
- **类型**: `string`
- **说明**: MCP服务器的HTTP/SSE端点URL
- **支持功能**: 环境变量替换
- **示例**: 
  - `"http://localhost:8080"`
  - `"https://mcp.amap.com/sse?key=${API_KEY}"`
  - `"https://api.example.com/mcp"`

## 配置示例

### 1. STDIO类型服务器 (本地Python脚本)

```json
{
  "fofa-mcp-server": {
    "description": "FOFA search engine MCP server for asset discovery",
    "command": "python",
    "args": ["/mcp_servers/fofa.py"],
    "env": {
      "FOFA_EMAIL": "${FOFA_EMAIL:-your_fofa_email@example.com}",
      "FOFA_KEY": "${FOFA_KEY:-your_fofa_api_key}",
      "PYTHONPATH": "/app"
    },
    "auto_connect": true,
    "enabled": true
  }
}
```

### 2. STDIO类型服务器 (Python模块)

```json
{
  "zoomeye-mcp-server": {
    "description": "ZoomEye search engine MCP server for asset discovery", 
    "command": "python",
    "args": ["-m", "mcp_server_zoomeye"],
    "env": {
      "ZOOMEYE_API_KEY": "${ZOOMEYE_API_KEY:-your_zoomeye_api_key}",
      "PYTHONPATH": "/app"
    },
    "auto_connect": true,
    "enabled": true
  }
}
```

### 3. HTTP类型服务器 (远程服务)

```json
{
  "amap-location": {
    "description": "Amap (高德地图) MCP server - Custom with your API key",
    "transport": "http",
    "url": "https://mcp.amap.com/sse?key=${AMAP_API_KEY}",
    "auto_connect": false,
    "enabled": false
  }
}
```

### 4. SSE类型服务器 (Server-Sent Events)

```json
{
  "mcp_server_sec_agent": {
    "description": "安全告警智能研判工具，支持结合原始告警数据、关联上下文及安全专家经验进行自动化分析",
    "transport": "http",
    "protocol": "sse",
    "url": "https://sec-agent.mcp.volcbiz.com/sse?token=${SEC_AGENT_TOKEN}",
    "auto_connect": true,
    "enabled": true
  }
}
```

**注意**:
- SSE服务器使用实时事件流进行通信
- 协议字段会根据URL自动检测（包含`/sse`时自动设为`"sse"`）
- Token通常直接包含在URL中作为查询参数

## 环境变量管理

### 变量替换语法

1. **简单替换**: `${VAR_NAME}`
   - 如果环境变量存在，使用其值
   - 如果不存在，保持原样

2. **默认值语法**: `${VAR_NAME:-default_value}`
   - 如果环境变量存在，使用其值
   - 如果不存在，使用默认值

### 推荐的环境变量

```bash
# FOFA配置
FOFA_EMAIL=your_email@example.com
FOFA_KEY=your_fofa_api_key

# ZoomEye配置  
ZOOMEYE_API_KEY=your_zoomeye_api_key

# 高德地图配置
AMAP_API_KEY=your_amap_api_key

# 安全代理配置
SEC_AGENT_TOKEN=your_security_agent_token
```

## 配置验证

### 自动配置标准化

系统会自动标准化配置：

1. **自动检测传输方式**:
   - 有`url`字段 → 设置`transport: "http"`
   - 有`command`字段 → 设置`transport: "stdio"`

2. **自动设置默认值**:
   - `enabled: true`
   - `auto_connect: true`
   - `description: "MCP Server: {server_id}"`

### 配置加载优先级

1. `/mcp_servers/config.json` (Docker容器内，最高优先级)
2. `mcp_servers/config.json` (开发环境)
3. `../mcp_servers/config.json` (相对路径)

## 故障排除

### 常见问题

1. **STDIO服务器连接失败**
   - 检查`command`和`args`是否正确
   - 验证脚本文件是否存在且可执行
   - 检查环境变量是否正确设置

2. **HTTP服务器连接失败**
   - 验证URL是否可访问
   - 检查API密钥是否有效
   - 确认网络连接正常

3. **环境变量未生效**
   - 确认环境变量在容器/进程中可用
   - 检查变量名称是否正确
   - 验证默认值语法

### 调试技巧

1. **查看日志**:
   ```bash
   docker logs ai-manus-5-mcp-client-1
   ```

2. **测试连接**:
   ```bash
   curl http://localhost:8001/api/mcp/servers/{server_id}/status
   ```

3. **列出工具**:
   ```bash
   curl http://localhost:8001/api/mcp/servers/{server_id}/tools
   ```

## 最佳实践

### 1. 安全配置
- 使用环境变量存储敏感信息(API密钥、Token)
- 不要在配置文件中硬编码密钥
- 使用默认值语法提供安全的回退值

### 2. 性能优化
- 将常用服务器设置为`auto_connect: true`
- 禁用不需要的服务器(`enabled: false`)
- 合理设置连接超时时间

### 3. 维护性
- 提供清晰的`description`
- 使用一致的命名规范
- 定期更新和验证配置

## 扩展指南

### 添加新的MCP服务器

1. 在`preset_servers`中添加新条目
2. 根据服务器类型选择合适的传输方式
3. 配置必要的认证信息
4. 测试连接和工具可用性
5. 更新相关文档

### 自定义MCP服务器

参考现有服务器实现，创建符合MCP协议的服务器，支持以下方法：
- `initialize`: 初始化连接
- `tools/list`: 列出可用工具
- `tools/call`: 调用指定工具

---

**注意**: 配置更改后需要重启MCP客户端服务才能生效。 