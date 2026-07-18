# 🚀 Quick Start

## Environment Requirements

This project mainly relies on Docker for development and deployment, requiring a newer version of Docker:

 * Docker 20.10+
 * Docker Compose

Model capabilities required:

 * Supports LangChain chat models (default provider is `openai`)
 * Native tool / function calling (plans and step results are submitted via structured output tools — not JSON-in-prompt)

Recommended models: Deepseek and ChatGPT with reliable tool calling.

## Docker Installation

### Windows & Mac Systems

Install Docker Desktop according to official requirements: https://docs.docker.com/desktop/

### Linux Systems

Install Docker Engine according to official requirements: https://docs.docker.com/engine/

## Deployment

Deploy using Docker Compose. All configuration is managed through a `.env` file (via `env_file`):

<!-- docker-compose-example.yml -->
```yaml
services:
  frontend:
    image: simpleyyt/manus-frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - manus-network
    environment:
      - BACKEND_URL=http://backend:8000

  backend:
    image: simpleyyt/manus-backend
    depends_on:
      - sandbox
      - claw
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      #- ./mcp.json:/etc/mcp.json # Mount MCP servers directory
    networks:
      - manus-network
    env_file:
      # All configuration is loaded from the .env file, see .env.example
      # More configuration options: https://docs.ai-manus.com/#/configuration
      - .env

  sandbox:
    image: simpleyyt/manus-sandbox
    command: /bin/sh -c "exit 0"  # prevent sandbox from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  claw:
    image: simpleyyt/manus-claw
    entrypoint: /bin/sh -c "exit 0"  # prevent claw from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  mongodb:
    image: mongo:7.0
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
    #ports:
    #  - "27017:27017"
    networks:
      - manus-network

  redis:
    image: redis:7.0
    restart: unless-stopped
    networks:
      - manus-network

volumes:
  mongodb_data:
    name: manus-mongodb-data

networks:
  manus-network:
    name: manus-network
    driver: bridge
```
<!-- /docker-compose-example.yml -->

Save as `docker-compose.yml` file.

### Create the `.env` Configuration File

Next to `docker-compose.yml`, create a `.env` file based on [`.env.example`](https://github.com/simpleyyt/ai-manus/blob/main/.env.example). At minimum set `API_KEY`, and adjust `API_BASE` and `MODEL_NAME` for your model service:

```ini
API_KEY=sk-xxxx
API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o
```

The full `.env.example` is shown below (search engine, authentication, sandbox, Claw, and more options):

<!-- .env.example -->
```ini
# Model provider configuration
API_KEY=
API_BASE=http://mockserver:8090/v1

# Model configuration
# MODEL_PROVIDER selects the LLM integration (via LangChain init_chat_model).
# Built-in providers: openai, deepseek, anthropic, ollama. OpenAI-compatible
# endpoints (DeepSeek / OneAPI / vLLM / ...) work with openai + API_BASE.
# See docs/configuration.md for per-provider examples.
MODEL_PROVIDER=openai
MODEL_NAME=deepseek-chat
TEMPERATURE=0.7
MAX_TOKENS=2000

# LLM gateway provider: langchain (default) or openai.
# - langchain: uses init_chat_model, supports many providers via MODEL_PROVIDER.
# - openai:    talks to OpenAI / OpenAI-compatible endpoints (API_BASE) directly
#              via the official openai Python SDK (MODEL_PROVIDER is ignored).
#LLM_PROVIDER=langchain

# MongoDB configuration
#MONGODB_URI=mongodb://mongodb:27017
#MONGODB_DATABASE=manus
#MONGODB_USERNAME=
#MONGODB_PASSWORD=

# Redis configuration
#REDIS_HOST=redis
#REDIS_PORT=6379
#REDIS_DB=0
#REDIS_PASSWORD=

# Sandbox configuration
#SANDBOX_ADDRESS=
SANDBOX_IMAGE=simpleyyt/manus-sandbox
SANDBOX_NAME_PREFIX=sandbox
SANDBOX_TTL_MINUTES=30
SANDBOX_NETWORK=manus-network
#SANDBOX_CHROME_ARGS=
#SANDBOX_HTTPS_PROXY=
#SANDBOX_HTTP_PROXY=
#SANDBOX_NO_PROXY=

# Browser engine configuration
# Options: playwright, browser_use (default)
# - playwright:   uses Playwright directly via CDP (stable, well-tested)
# - browser_use:  uses the browser_use library's BrowserSession via CDP
#                 (richer DOM state extraction via AI-friendly selector map)
#BROWSER_ENGINE=browser_use

# Search engine configuration
# Options: baidu, baidu_web, google, bing, bing_web, tavily, serper, custom
# baidu:    uses the Baidu Qianfan AI Search API (requires BAIDU_SEARCH_API_KEY)
# baidu_web: scrapes Baidu search results with browser impersonation (no API key needed)
# bing:     uses the official Bing Web Search API (requires BING_SEARCH_API_KEY)
# bing_web: scrapes Bing search results directly (no API key needed)
# tavily:   uses the Tavily Search API (requires TAVILY_API_KEY)
# serper:   uses the Serper.dev Google Search API (requires SERPER_API_KEY)
# custom:   calls any third-party search REST API via SEARCH_API_URL + SEARCH_API_KEY
SEARCH_PROVIDER=bing_web

# Baidu search configuration, only used when SEARCH_PROVIDER=baidu
# Get your API key from https://console.bce.baidu.com/qianfan/ais/console/onlineService
#BAIDU_SEARCH_API_KEY=

# Bing search configuration, only used when SEARCH_PROVIDER=bing
# Get your API key from https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
#BING_SEARCH_API_KEY=

# Google search configuration, only used when SEARCH_PROVIDER=google
#GOOGLE_SEARCH_API_KEY=
#GOOGLE_SEARCH_ENGINE_ID=

# Tavily search configuration, only used when SEARCH_PROVIDER=tavily
# Get your API key from https://tavily.com
#TAVILY_API_KEY=

# Serper.dev search configuration, only used when SEARCH_PROVIDER=serper
# Returns reliable Google results. Get your API key from https://serper.dev
#SERPER_API_KEY=

# Custom search API configuration, only used when SEARCH_PROVIDER=custom
# Allows integration with any third-party search REST API.
#
# Minimal setup (POST + Bearer token, e.g. a custom internal API):
#   SEARCH_API_URL=https://your-search-api.example.com/search
#   SEARCH_API_KEY=your-api-key
#
# Serper.dev via custom provider:
#   SEARCH_API_URL=https://google.serper.dev/search
#   SEARCH_API_KEY=your-serper-key
#   SEARCH_API_KEY_HEADER=X-API-KEY
#   SEARCH_API_KEY_HEADER_PREFIX=
#   SEARCH_RESULT_FIELD=organic
#
# SerpAPI via custom provider:
#   SEARCH_API_URL=https://serpapi.com/search
#   SEARCH_API_KEY=your-serpapi-key
#   SEARCH_API_KEY_PARAM=api_key
#   SEARCH_API_METHOD=GET
#   SEARCH_RESULT_FIELD=organic_results
#
# Brave Search API via custom provider:
#   SEARCH_API_URL=https://api.search.brave.com/res/v1/web/search
#   SEARCH_API_KEY=your-brave-key
#   SEARCH_API_KEY_HEADER=X-Subscription-Token
#   SEARCH_API_KEY_HEADER_PREFIX=
#   SEARCH_API_METHOD=GET
#   SEARCH_RESULT_FIELD=web.results
#   SEARCH_SNIPPET_FIELD=description
#
#SEARCH_API_URL=
#SEARCH_API_KEY=
#SEARCH_API_KEY_HEADER=Authorization
#SEARCH_API_KEY_HEADER_PREFIX=Bearer
#SEARCH_API_KEY_PARAM=
#SEARCH_API_METHOD=POST
#SEARCH_QUERY_FIELD=q
#SEARCH_RESULT_FIELD=results
#SEARCH_TITLE_FIELD=title
#SEARCH_LINK_FIELD=link
#SEARCH_SNIPPET_FIELD=snippet

# Google Analytics configuration
# Set your Google Analytics Measurement ID (e.g. G-XXXXXXXXXX)
#GOOGLE_ANALYTICS_ID=

# Auth configuration
# Options: password, none, local
AUTH_PROVIDER=password

# Password auth configuration, only used when AUTH_PROVIDER=password
PASSWORD_SALT=
PASSWORD_HASH_ROUNDS=10

# Local auth configuration, only used when AUTH_PROVIDER=local
#LOCAL_AUTH_EMAIL=admin@example.com
#LOCAL_AUTH_PASSWORD=admin

# JWT configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email configuration
# Only used when AUTH_PROVIDER=password
#EMAIL_HOST=smtp.gmail.com
#EMAIL_PORT=587
#EMAIL_USERNAME=your-email@gmail.com
#EMAIL_PASSWORD=your-password
#EMAIL_FROM=your-email@gmail.com

# Claw (OpenClaw) configuration
# Enable or disable Claw feature (hides sidebar entry when false)
#CLAW_ENABLED=false
# Docker image used for Claw containers
#CLAW_IMAGE=simpleyyt/manus-claw
# Prefix for Claw container names
#CLAW_NAME_PREFIX=manus-claw
# Time-to-live for Claw containers in seconds (0 = unlimited)
#CLAW_TTL_SECONDS=3600
# Docker network bridge name for Claw containers
#CLAW_NETWORK=manus-network
# Max seconds to wait for Claw container to become ready
#CLAW_READY_TIMEOUT=300
# Fixed Claw address (for development; skips Docker container creation)
#CLAW_ADDRESS=
# Static API key for Claw (for development / fixed container)
#CLAW_API_KEY=
# Backend API URL used by Claw containers for callbacks
#MANUS_API_BASE_URL=http://backend:8000

# Extra headers for LLM API requests (JSON format)
#EXTRA_HEADERS={"X-Custom-Header": "value"}

# Task backend configuration
# local: run agent tasks in-process (default)
# celery: run agent tasks on distributed Celery workers
#         (requires a worker container, see docs/configuration.md)
#TASK_BACKEND=local
# Optional custom Celery broker URL (defaults to the Redis settings above)
#CELERY_BROKER_URL=

# MCP configuration
#MCP_CONFIG_PATH=/etc/mcp.json

# Log configuration
LOG_LEVEL=INFO
```
<!-- /.env.example -->

> **Tip**: `env_file` and `environment` can be used together — values in `environment` override those from `env_file`. See [Configuration](configuration.md) for a full list of available options.

### Start Services

```bash
docker compose up -d
```

> Note: If you see `sandbox-1 exited with code 0`, this is normal — it ensures the sandbox image is successfully pulled locally.

Open your browser and visit <http://localhost:5173> to access Manus.

## Local Development Smoke Test

For day-to-day development, use the hot-reload stack:

```bash
cp .env.example .env
# For local smoke tests you can set AUTH_PROVIDER=none and point API_BASE at mockserver or a real LLM
./dev.sh up -d
```

Open <http://localhost:5173>. In debug mode only one shared sandbox is started (`SANDBOX_ADDRESS=sandbox`). See the root README “Development Guide” for more.
