# 📋 Configuration Guide

## Configuration Items

### Model Provider Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `API_KEY` | - | Yes | API key for the LLM model |
| `API_BASE` | `http://mockserver:8090/v1` | No | Base API address for specifying model service endpoint |

### Model Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `MODEL_PROVIDER` | `openai` | No | Model provider (e.g. `openai`, `anthropic`, `google_genai`, `ollama`) |
| `MODEL_NAME` | `deepseek-chat` | Yes | Name of the model to use |
| `TEMPERATURE` | `0.7` | No | Randomness level of model responses, range 0-1 |
| `MAX_TOKENS` | `2000` | No | Maximum number of tokens in model response |

### MongoDB Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `MONGODB_URI` | `mongodb://mongodb:27017` | No | MongoDB connection string |
| `MONGODB_DATABASE` | `manus` | No | Database name |
| `MONGODB_USERNAME` | - | No | MongoDB username |
| `MONGODB_PASSWORD` | - | No | MongoDB password |

> **Note**: MongoDB configuration items are currently commented out, indicating they may be optional features or not fully implemented yet.

### Redis Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `REDIS_HOST` | `redis` | No | Redis server address |
| `REDIS_PORT` | `6379` | No | Redis server port |
| `REDIS_DB` | `0` | No | Redis database number |
| `REDIS_PASSWORD` | - | No | Redis password |

> **Note**: Redis configuration items are currently commented out, indicating they may be optional features or not fully implemented yet.

### Sandbox Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `SANDBOX_ADDRESS` | - | No | Sandbox server address |
| `SANDBOX_IMAGE` | `simpleyyt/manus-sandbox` | No | Docker sandbox image name |
| `SANDBOX_NAME_PREFIX` | `sandbox` | No | Sandbox container name prefix |
| `SANDBOX_TTL_MINUTES` | `30` | No | Sandbox time-to-live in minutes |
| `SANDBOX_NETWORK` | `manus-network` | No | Docker network name |
| `SANDBOX_CHROME_ARGS` | - | No | Chrome browser startup arguments |
| `SANDBOX_HTTPS_PROXY` | - | No | HTTPS proxy settings |
| `SANDBOX_HTTP_PROXY` | - | No | HTTP proxy settings |
| `SANDBOX_NO_PROXY` | - | No | List of addresses to exclude from proxy |

### Search Engine Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `SEARCH_PROVIDER` | `bing_web` | No | Search engine provider (`baidu`, `baidu_web`, `google`, `bing`, `bing_web`, or `tavily`) |

#### Baidu Search Configuration

Used only when `SEARCH_PROVIDER=baidu` (Baidu Qianfan AI Search API):

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `BAIDU_SEARCH_API_KEY` | - | Yes | Baidu Qianfan AI Search API key, get from [Baidu Qianfan Console](https://console.bce.baidu.com/qianfan/ais/console/onlineService) |

> If you don't want to apply for an API key, set `SEARCH_PROVIDER` to `baidu_web` to scrape Baidu search results directly without any key.

#### Bing Search Configuration

Used only when `SEARCH_PROVIDER=bing` (official API):

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `BING_SEARCH_API_KEY` | - | Yes | Bing Web Search API key, get from [Azure](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) |

> If you don't want to apply for an API key, set `SEARCH_PROVIDER` to `bing_web` to scrape Bing search results directly without any key.

#### Google Search Configuration

Used only when `SEARCH_PROVIDER=google`:

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `GOOGLE_SEARCH_API_KEY` | - | Yes | Google Search API key |
| `GOOGLE_SEARCH_ENGINE_ID` | - | Yes | Google Custom Search Engine ID |

#### Tavily Search Configuration

Used only when `SEARCH_PROVIDER=tavily`:

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `TAVILY_API_KEY` | - | Yes | Tavily Search API key |

### Authentication Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `AUTH_PROVIDER` | `password` | No | Authentication provider (`password`, `none`, or `local`) |
| `SHOW_GITHUB_BUTTON` | `true` | No | Whether to show the GitHub button in the top bar |
| `GITHUB_REPOSITORY_URL` | `https://github.com/simpleyyt/ai-manus` | No | GitHub button target URL |

#### Password Authentication Configuration

Used only when `AUTH_PROVIDER=password`:

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `PASSWORD_SALT` | - | No | Password encryption salt |
| `PASSWORD_HASH_ROUNDS` | `10` | No | Password hash rounds |

#### Local Authentication Configuration

Used only when `AUTH_PROVIDER=local`:

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `LOCAL_AUTH_EMAIL` | `admin@example.com` | No | Local admin email |
| `LOCAL_AUTH_PASSWORD` | `admin` | No | Local admin password |

### Frontend Runtime Config API

Frontend fetches runtime config from an independent config domain endpoint:

- `GET /api/v1/config/frontend`
- response fields:
  - `auth_provider`
  - `show_github_button`
  - `github_repository_url`

This endpoint is independent from `/api/v1/auth/*` and is used for frontend runtime behavior and feature toggles.

### JWT Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `JWT_SECRET_KEY` | `your-secret-key-here` | Yes | JWT signing key (must be changed in production) |
| `JWT_ALGORITHM` | `HS256` | No | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | No | Access token expiration time in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | No | Refresh token expiration time in days |

### Email Configuration

Used only when `AUTH_PROVIDER=password`:

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `EMAIL_HOST` | - | No | SMTP server address |
| `EMAIL_PORT` | `587` | No | SMTP server port |
| `EMAIL_USERNAME` | - | No | Email username |
| `EMAIL_PASSWORD` | - | No | Email password |
| `EMAIL_FROM` | - | No | Sender email address |

### MCP Configuration

| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `MCP_CONFIG_PATH` | `/etc/mcp.json` | No | MCP configuration file path |

### Log Configuration
| Configuration | Default Value | Required | Description |
|---------------|---------------|----------|-------------|
| `LOG_LEVEL` | `INFO` | No | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

