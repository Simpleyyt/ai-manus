# AI Manus × Claw 后端服务

[English](README.md) | 中文

AI Manus × Claw 是一个基于 FastAPI 和 LangChain Chat Model 的智能对话代理系统。该后端采用领域驱动设计(DDD)架构，支持智能对话、文件操作、Shell命令执行、浏览器自动化，以及集成 [OpenClaw](https://github.com/anthropics/openclaw) AI 助手管理（Claw）等功能。

## 项目架构

项目采用领域驱动设计(DDD)架构，清晰地分离各层职责：

```
backend/
├── app/
│   ├── domain/          # 领域层：包含核心业务逻辑
│   │   ├── models/      # 领域模型定义
│   │   ├── services/    # 领域服务（agents、tools、prompts、flows）
│   │   └── external/    # 外部服务接口（Protocol）
│   ├── application/     # 应用层：编排业务流程
│   │   └── services/    # 应用服务（agent、auth、file、token、email、claw）
│   ├── interfaces/      # 接口层：定义系统对外接口
│   │   ├── api/         # API 路由（会话、文件、认证、配置、Claw、OpenAI 代理）
│   │   └── schemas/     # 请求/响应与 SSE 事件模式
│   ├── infrastructure/  # 基础设施层：提供技术实现
│   ├── core/            # 核心配置（config.py）
│   └── main.py          # 应用入口
├── Dockerfile           # Docker配置文件
├── pyproject.toml       # 项目依赖与元数据
└── README.md            # 项目文档
```

## 核心功能

1. **会话管理**：创建和管理对话会话实例
2. **实时对话**：通过Server-Sent Events (SSE)实现实时对话
3. **工具调用**：支持多种工具调用，包括：
   - 浏览器自动化操作（使用Playwright）
   - Shell命令执行与查看
   - 文件读写操作
   - 网络搜索集成
4. **沙盒环境**：使用Docker容器提供隔离的执行环境
5. **VNC可视化**：通过WebSocket连接支持远程查看沙盒环境
6. **Claw（Manus × Claw）**：为每个用户管理 OpenClaw 容器生命周期，合并聊天历史（MongoDB + OpenClaw `.jsonl` 会话），WebSocket 实时通信，文件上传/解析，以及为 Claw 容器提供 OpenAI 兼容 LLM 代理

## 环境要求

- Python 3.12+
- Docker 20.10+
- MongoDB 4.4+
- Redis 6.0+

## 安装配置

1. **安装 uv**:
```bash
pip install uv
```

2. **安装依赖**:
```bash
uv sync
```

3. **环境变量配置**:
创建 `.env` 文件并设置以下环境变量（完整列表见 `app/core/config.py` 或根目录 [.env.example](https://github.com/simpleyyt/ai-manus/blob/main/.env.example)）:
```
# Model provider configuration
API_KEY=your_api_key_here                # 模型供应商 API 密钥（必填）
API_BASE=https://api.openai.com/v1       # 模型 API 基础 URL（部分供应商可选）

# Model configuration
MODEL_NAME=gpt-4o                        # 使用的模型名称
MODEL_PROVIDER=openai                    # LangChain 模型供应商
LLM_PROVIDER=langchain                   # LLM 网关: langchain（默认）或 openai（OpenAI SDK）
TEMPERATURE=0.7                          # 模型温度参数
MAX_TOKENS=2000                          # 模型单次请求最大输出 token 数量

# Search engine configuration
SEARCH_PROVIDER=bing_web                 # baidu / baidu_web / google / bing / bing_web / tavily / serper / custom
GOOGLE_SEARCH_API_KEY=                   # Google Search API 密钥（SEARCH_PROVIDER=google）
GOOGLE_SEARCH_ENGINE_ID=                 # Google 自定义搜索引擎 ID（SEARCH_PROVIDER=google）

# Sandbox configuration
SANDBOX_ADDRESS=                         # 固定沙盒地址（开发用）；未设置时按会话创建容器
SANDBOX_IMAGE=simpleyyt/manus-sandbox    # 沙盒环境 Docker 镜像
SANDBOX_NAME_PREFIX=sandbox              # 沙盒容器名称前缀
SANDBOX_TTL_MINUTES=30                   # 沙盒容器生存时间（分钟）
SANDBOX_NETWORK=manus-network            # Docker 网络名称，用于沙盒容器间通信

# Authentication configuration
AUTH_PROVIDER=password                   # password / local / none
JWT_SECRET_KEY=your-secret-key-here      # JWT 签名密钥（生产环境必须设置）

# Claw (OpenClaw) configuration
CLAW_ENABLED=false                       # 是否启用 Claw 集成
CLAW_IMAGE=simpleyyt/manus-claw          # Claw 容器 Docker 镜像
CLAW_TTL_SECONDS=3600                    # Claw 容器生存时间（秒）

# MCP configuration
MCP_CONFIG_PATH=/etc/mcp.json            # 外部 MCP 服务配置文件路径

# Task backend configuration
TASK_BACKEND=local                       # local（进程内 asyncio）或 celery（分布式 worker）

# Database configuration
MONGODB_URI=mongodb://localhost:27017    # MongoDB 连接 URL
MONGODB_DATABASE=manus                   # MongoDB 数据库名称
REDIS_HOST=localhost                     # Redis 主机地址
REDIS_PORT=6379                          # Redis 端口
REDIS_DB=0                               # Redis 数据库编号

# Log configuration
LOG_LEVEL=INFO                           # 日志级别，可选: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 运行方式

### 开发环境
```bash
# 启动开发服务器（带热重载功能）
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 http://localhost:8000 启动。

### Docker部署
```bash
# 构建Docker镜像
docker build -t manus-ai-agent .

# 运行容器
docker run -p 8000:8000 --env-file .env -v /var/run/docker.sock:/var/run/docker.sock manus-ai-agent
```

> 注意：如果使用Docker部署，需要挂载Docker套接字以便后端可以创建沙盒容器。

## API接口文档

基础URL: `/api/v1`。服务运行时可通过 `/docs` 访问交互式 Swagger UI。

所有 JSON 接口返回统一格式：
```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

### 会话接口（`/api/v1/sessions`）

| 方法 | 路径 | 描述 |
|---|---|---|
| PUT | `/sessions` | 创建新的对话会话 |
| GET | `/sessions` | 获取所有会话列表 |
| POST | `/sessions` | 以 SSE 流式获取会话列表更新 |
| GET | `/sessions/{session_id}` | 获取会话详情（包括事件历史） |
| DELETE | `/sessions/{session_id}` | 删除会话 |
| POST | `/sessions/{session_id}/stop` | 停止活跃的会话 |
| POST | `/sessions/{session_id}/chat` | 发送消息并接收 SSE 事件流 |
| POST | `/sessions/{session_id}/clear_unread_message_count` | 清除未读消息计数 |
| POST | `/sessions/{session_id}/shell` | 查看沙盒中的 Shell 会话输出 |
| POST | `/sessions/{session_id}/file` | 查看沙盒中的文件内容 |
| GET | `/sessions/{session_id}/files` | 获取会话关联的文件列表 |
| WebSocket | `/sessions/{session_id}/vnc` | 与沙盒建立 VNC 连接（binary 子协议） |
| POST | `/sessions/{session_id}/vnc/signed-url` | 生成 VNC WebSocket 访问签名 URL |
| POST | `/sessions/{session_id}/share` | 公开分享会话 |
| DELETE | `/sessions/{session_id}/share` | 取消分享会话 |
| GET | `/sessions/{session_id}/share/files` | 获取已分享会话的文件列表 |
| GET | `/sessions/shared/{session_id}` | 获取已分享会话（无需认证） |

`/chat` 输出的 SSE 事件类型：`message`、`title`、`plan`、`step`、`tool`、`wait`、`error`、`done`。

### 文件接口（`/api/v1/files`）

| 方法 | 路径 | 描述 |
|---|---|---|
| POST | `/files` | 上传文件 |
| GET | `/files/{file_id}` | 下载文件（支持签名访问令牌） |
| GET | `/files/{file_id}/download` | 以附件形式下载文件 |
| DELETE | `/files/{file_id}` | 删除文件 |
| GET | `/files/{file_id}/info` | 获取文件元信息 |
| POST | `/files/{file_id}/signed-url` | 生成签名下载 URL |

### 认证接口（`/api/v1/auth`）

| 方法 | 路径 | 描述 |
|---|---|---|
| POST | `/auth/login` | 登录 |
| POST | `/auth/register` | 注册新用户 |
| GET | `/auth/status` | 获取认证提供方状态 |
| GET | `/auth/me` | 获取当前用户信息 |
| POST | `/auth/refresh` | 刷新访问令牌 |
| POST | `/auth/logout` | 登出 |
| POST | `/auth/change-password` | 修改密码 |
| POST | `/auth/change-fullname` | 修改用户名称 |
| POST | `/auth/send-verification-code` | 发送邮箱验证码 |
| POST | `/auth/reset-password` | 通过验证码重置密码 |
| GET | `/auth/user/{user_id}` | 按 ID 获取用户 |
| POST | `/auth/user/{user_id}/activate` | 激活用户 |
| POST | `/auth/user/{user_id}/deactivate` | 停用用户 |

### Claw 接口（`/api/v1/claw`）

| 方法 | 路径 | 描述 |
|---|---|---|
| GET | `/claw` | 获取当前用户的 Claw 实例 |
| POST | `/claw` | 为当前用户创建 Claw 实例 |
| DELETE | `/claw` | 删除当前用户的 Claw 实例 |
| GET | `/claw/api-key` | 获取用于 LLM 代理认证的用户级 API 密钥 |
| GET | `/claw/history` | 获取合并后的 Claw 聊天历史 |
| POST | `/claw/upload` | 从 Claw 工作区上传文件（Claw API 密钥认证） |
| GET | `/claw/files/{filename}` | 代理下载 Claw 工作区中的文件 |
| GET | `/claw/resolve/{file_id}` | 解析 `manus-file://` 元信息（Claw API 密钥认证） |
| GET | `/claw/resolve/{file_id}/download` | 下载 `manus-file://` 内容（Claw API 密钥认证） |
| WebSocket | `/claw/ws` | Claw 聊天的持久 WebSocket 连接 |

### 其它接口

| 方法 | 路径 | 描述 |
|---|---|---|
| GET | `/api/v1/config/frontend` | 前端运行时配置 |
| POST | `/v1/chat/completions` | 供 Claw 容器使用的 OpenAI 兼容 LLM 代理 |

## 错误处理

所有API在发生错误时会返回统一格式的响应：
```json
{
  "code": 400,
  "msg": "错误描述",
  "data": null
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 开发指南

### 添加新工具

1. 在 `domain/external` 目录下定义 Protocol 接口
2. 在 `infrastructure/external` 层实现功能
3. 在 `interfaces/dependencies.py` 中完成依赖注入
4. 如需供 Agent 调用，在 `domain/services/tools` 中封装为工具集
