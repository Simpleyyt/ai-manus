# 🚀 快速开始

> **⚠️ 重要提示**
> 
> **第一步**：复制配置模板  
> ```bash
> cp config.json.example config.json
> ```
> 
> **第二步**：编辑 `config.json` 文件，添加或删除你的 MCP 服务器配置  
> 具体配置方法请参考下方详细说明。



# MCP服务器配置指南

## 📖 目录

- [🚀 快速开始](#-快速开始)
- [📖 目录](#-目录)
- [📁 配置文件位置](#-配置文件位置)
- [配置文件结构](#配置文件结构)
- [服务器配置字段详解](#服务器配置字段详解)
- [📝 配置示例](#-配置示例)
- [环境变量管理](#环境变量管理)
- [配置验证](#配置验证)
- [🔧 故障排除](#-故障排除)
- [最佳实践](#最佳实践)
- [扩展指南](#扩展指南)
- [📋 版本兼容性](#-版本兼容性)
- [🔗 相关链接](#-相关链接)
- [📞 技术支持](#-技术支持)

## 概述

本文档详细说明了`ai-manus`中MCP (Model Context Protocol) 服务器的配置文件`config.json`的字段含义、配置方法和最佳实践。

## 📁 配置文件位置

| 环境 | 路径 | 说明 |
|------|------|------|
| **Docker容器** | `/mcp_servers/config.json` | 容器内的配置文件路径 |
| **开发环境** | `ai-manus/mcp-client/mcp_servers/config.json` | 本地开发时的配置文件 |
| **相对路径** | `mcp_servers/config.json` | 相对于应用根目录的路径 |

> 💡 **提示**：系统会按照上述顺序查找配置文件，使用找到的第一个文件。

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

## 📝 配置示例

> 以下是经过测试的配置示例，您可以直接复制使用并修改相应的API密钥。

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

```

### 3. SSE类型服务器 (Server-Sent Events)

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

建议在`.env`文件或Docker环境中设置以下变量：

```bash
# FOFA配置 - 网络空间资产搜索引擎
FOFA_EMAIL=your_email@example.com
FOFA_KEY=your_fofa_api_key

# ZoomEye配置 - 网络空间搜索引擎
ZOOMEYE_API_KEY=your_zoomeye_api_key

# 高德地图配置 - 地理位置服务
AMAP_API_KEY=your_amap_api_key

# 安全代理配置 - 安全告警智能研判
SEC_AGENT_TOKEN=your_security_agent_token

# 其他常用配置
PYTHONPATH=/app
LOG_LEVEL=INFO
MCP_TIMEOUT=30
```

> 💡 **安全提示**：
> - 不要将API密钥提交到版本控制系统
> - 使用`.env`文件管理本地开发环境的敏感信息
> - 在生产环境中使用Docker secrets或其他安全方式管理密钥

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

## 🔧 故障排除

### 常见问题

#### 1. **STDIO服务器连接失败**
   - ✅ 检查`command`和`args`是否正确
   - ✅ 验证脚本文件是否存在且可执行
   - ✅ 检查环境变量是否正确设置
   - ✅ 确认Python/Node.js等运行环境已安装
   - ✅ 检查文件权限是否允许执行

#### 2. **HTTP服务器连接失败**
   - ✅ 验证URL是否可访问（可用curl测试）
   - ✅ 检查API密钥是否有效且未过期
   - ✅ 确认网络连接正常
   - ✅ 检查防火墙设置
   - ✅ 验证SSL证书是否有效（HTTPS连接）

#### 3. **环境变量未生效**
   - ✅ 确认环境变量在容器/进程中可用
   - ✅ 检查变量名称是否正确（区分大小写）
   - ✅ 验证默认值语法：`${VAR:-default}`
   - ✅ 检查.env文件是否正确加载

#### 4. **服务器启动但工具不可用**
   - ✅ 检查MCP服务器是否正确实现了MCP协议
   - ✅ 验证工具权限和依赖项
   - ✅ 查看服务器日志获取详细错误信息

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


## 🔗 相关链接

- [MCP协议官方文档](https://modelcontextprotocol.io)
- [ai-manus项目文档](../README.md)
- [MCP服务器开发指南](./MCP_SERVER_DEVELOPMENT.md)

## 📞 技术支持

如果在配置过程中遇到问题，可以：

1. 📖 查看本文档的故障排除部分
2. 🔍 检查应用日志文件
3. 💬 在项目Issue中提交问题
4. 📧 联系技术支持团队

---

> **⚠️ 重要提醒**：配置更改后需要重启MCP客户端服务才能生效。
> 
> ```bash
> # Docker环境重启
> docker-compose restart mcp-client
> 
> # 开发环境重启
> # 停止当前服务，然后重新启动
> ``` 