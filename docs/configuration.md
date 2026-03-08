# 📋 配置说明

## 配置项

### 模型提供商配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `API_KEY` | - | 是 | LLM 模型的 API 密钥 |
| `API_BASE` | `http://mockserver:8090/v1` | 否 | API 基础地址，用于指定模型服务的端点 |
| `EXTRA_HEADERS` | - | 否 | 额外请求头，支持 JSON（如 `{"x-a":"1"}`）或 `k:v,k2:v2` 格式 |

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

### 搜索引擎配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `SEARCH_PROVIDER` | `bing` | 否 | 搜索引擎提供商 (`baidu`、`google` 或 `bing`) |

#### Google 搜索配置

仅当 `SEARCH_PROVIDER=google` 时使用：

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `GOOGLE_SEARCH_API_KEY` | - | 是 | Google 搜索 API 密钥 |
| `GOOGLE_SEARCH_ENGINE_ID` | - | 是 | Google 自定义搜索引擎 ID |

### 认证配置

| 配置项 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| `AUTH_PROVIDER` | `password` | 否 | 认证提供商 (`password`、`none` 或 `local`) |

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


