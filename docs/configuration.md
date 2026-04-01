# 📋 配置说明

## 配置项

### 模型提供商配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `API_KEY` | - | 是 | LLM 模型的 API 密钥 |
| `API_BASE` | `http://mockserver:8090/v1` | 否 | API 基础地址，用于指定模型服务的端点 |

### 模型配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `MODEL_PROVIDER` | `openai` | 否 | 模型提供商（如 `openai`、`anthropic`、`google_genai`、`ollama`） |
| `MODEL_NAME` | `deepseek-chat` | 是 | 要使用的模型名称 |
| `TEMPERATURE` | `0.7` | 否 | 模型响应的随机性程度，范围 0-1 |
| `MAX_TOKENS` | `2000` | 否 | 模型响应的最大 token 数量 |

### MongoDB 配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `MONGODB_URI` | `mongodb://mongodb:27017` | 否 | MongoDB 连接字符串 |
| `MONGODB_DATABASE` | `manus` | 否 | 数据库名称 |
| `MONGODB_USERNAME` | - | 否 | MongoDB 用户名 |
| `MONGODB_PASSWORD` | - | 否 | MongoDB 密码 |

> **注意**: MongoDB 配置项当前被注释，表示可能是可选功能或尚未完全实现。

### Redis 配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `REDIS_HOST` | `redis` | 否 | Redis 服务器地址 |
| `REDIS_PORT` | `6379` | 否 | Redis 服务器端口 |
| `REDIS_DB` | `0` | 否 | Redis 数据库编号 |
| `REDIS_PASSWORD` | - | 否 | Redis 密码 |

> **注意**: Redis 配置项当前被注释，表示可能是可选功能或尚未完全实现。

### 沙箱配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `SANDBOX_ADDRESS` | - | 否 | 沙箱服务器地址 |
| `SANDBOX_IMAGE` | `simpleyyt/manus-sandbox` | 否 | Docker 沙箱镜像名称 |
| `SANDBOX_NAME_PREFIX` | `sandbox` | 否 | 沙箱容器名称前缀 |
| `SANDBOX_TTL_MINUTES` | `30` | 否 | 沙箱生存时间（分钟） |
| `SANDBOX_NETWORK` | `manus-network` | 否 | Docker 网络名称 |
| `SANDBOX_CHROME_ARGS` | - | 否 | Chrome 浏览器启动参数 |
| `SANDBOX_HTTPS_PROXY` | - | 否 | HTTPS 代理设置 |
| `SANDBOX_HTTP_PROXY` | - | 否 | HTTP 代理设置 |
| `SANDBOX_NO_PROXY` | - | 否 | 不使用代理的地址列表 |

### Claw (OpenClaw) 配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `CLAW_ENABLED` | `true` | 否 | 是否启用 Claw 功能，设为 `false` 关闭左侧面板入口 |
| `CLAW_IMAGE` | `simpleyyt/manus-claw` | 否 | Claw Docker 镜像名称 |
| `CLAW_NAME_PREFIX` | `manus-claw` | 否 | Claw 容器名称前缀 |
| `CLAW_TTL_SECONDS` | `3600` | 否 | Claw 容器生存时间（秒），设为 `0` 表示不限时 |
| `CLAW_NETWORK` | - | 否 | Claw 容器使用的 Docker 网络桥名称 |
| `CLAW_READY_TIMEOUT` | `300` | 否 | 等待 Claw 容器就绪的最大秒数（默认 5 分钟） |
| `CLAW_ADDRESS` | - | 否 | 固定 Claw 地址（开发环境使用，设置后跳过 Docker 容器创建） |
| `CLAW_API_KEY` | - | 否 | 静态 API 密钥（开发环境 / 固定容器使用） |
| `MANUS_API_BASE_URL` | `http://backend:8000` | 否 | 后端 API 地址，供 Claw 容器回调使用 |

### 搜索引擎配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `SEARCH_PROVIDER` | `bing_web` | 否 | 搜索引擎提供商 (`baidu`、`baidu_web`、`google`、`bing`、`bing_web` 或 `tavily`) |

#### 百度搜索配置

仅当 `SEARCH_PROVIDER=baidu` 时使用（通过百度千帆 AI 搜索 API）：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `BAIDU_SEARCH_API_KEY` | - | 是 | 百度千帆 AI 搜索 API 密钥，从[百度千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/onlineService)获取 |

> 若不想申请 API 密钥，可将 `SEARCH_PROVIDER` 设为 `baidu_web`，直接通过网页抓取百度搜索结果，无需任何密钥。

#### Bing 搜索配置

仅当 `SEARCH_PROVIDER=bing` 时使用（通过官方 API 搜索）：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `BING_SEARCH_API_KEY` | - | 是 | Bing Web Search API 密钥，从 [Azure](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) 获取 |

> 若不想申请 API 密钥，可将 `SEARCH_PROVIDER` 设为 `bing_web`，直接通过网页抓取 Bing 搜索结果，无需任何密钥。

#### Google 搜索配置

仅当 `SEARCH_PROVIDER=google` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `GOOGLE_SEARCH_API_KEY` | - | 是 | Google 搜索 API 密钥 |
| `GOOGLE_SEARCH_ENGINE_ID` | - | 是 | Google 自定义搜索引擎 ID |

#### Tavily 搜索配置

仅当 `SEARCH_PROVIDER=tavily` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `TAVILY_API_KEY` | - | 是 | Tavily 搜索 API 密钥 |

### 认证配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `AUTH_PROVIDER` | `password` | 否 | 认证提供商 (`password`、`none` 或 `local`) |
| `SHOW_GITHUB_BUTTON` | `true` | 否 | 是否在前端显示 GitHub 按钮 |
| `GITHUB_REPOSITORY_URL` | `https://github.com/simpleyyt/ai-manus` | 否 | 前端 GitHub 按钮跳转地址 |
#### 密码认证配置

仅当 `AUTH_PROVIDER=password` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `PASSWORD_SALT` | - | 否 | 密码加密盐值 |
| `PASSWORD_HASH_ROUNDS` | `10` | 否 | 密码哈希轮数 |

#### 本地认证配置

仅当 `AUTH_PROVIDER=local` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `LOCAL_AUTH_EMAIL` | `admin@example.com` | 否 | 本地管理员邮箱 |
| `LOCAL_AUTH_PASSWORD` | `admin` | 否 | 本地管理员密码 |

### JWT 配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `JWT_SECRET_KEY` | `your-secret-key-here` | 是 | JWT 签名密钥（生产环境必须更改） |
| `JWT_ALGORITHM` | `HS256` | 否 | JWT 签名算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | 否 | 访问令牌过期时间（分钟） |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | 否 | 刷新令牌过期时间（天） |

### 邮箱配置

仅当 `AUTH_PROVIDER=password` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `EMAIL_HOST` | - | 否 | SMTP 服务器地址 |
| `EMAIL_PORT` | `587` | 否 | SMTP 服务器端口 |
| `EMAIL_USERNAME` | - | 否 | 邮箱用户名 |
| `EMAIL_PASSWORD` | - | 否 | 邮箱密码 |
| `EMAIL_FROM` | - | 否 | 发件人邮箱地址 |

### MCP 配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `MCP_CONFIG_PATH` | `/etc/mcp.json` | 否 | MCP 配置文件路径 |

### 日志配置
| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `LOG_LEVEL` | `INFO` | 否 | 日志级别 (`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`) |


