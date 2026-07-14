# AI Manus × Claw Backend Service

English | [中文](README_zh.md)

AI Manus × Claw is an intelligent conversation agent system based on FastAPI and LangChain chat models. The backend adopts Domain-Driven Design (DDD) architecture, supporting intelligent dialogue, file operations, Shell command execution, browser automation, and integrated [OpenClaw](https://github.com/anthropics/openclaw) AI assistant management (Claw).

## Project Architecture

The project adopts Domain-Driven Design (DDD) architecture, clearly separating the responsibilities of each layer:

```
backend/
├── app/
│   ├── domain/          # Domain layer: contains core business logic
│   │   ├── models/      # Domain model definitions
│   │   ├── services/    # Domain services
│   │   ├── external/    # External service interfaces
│   │   └── prompts/     # Prompt templates
│   ├── application/     # Application layer: orchestrates business processes
│   │   ├── services/    # Application services (agent, auth, file, token, email, claw)
│   │   └── schemas/     # Data schema definitions
│   ├── interfaces/      # Interface layer: defines external system interfaces
│   │   ├── api/         # API routes (sessions, files, auth, config, claw, OpenAI proxy)
│   │   └── schemas/     # Request/response and SSE event schemas
│   ├── infrastructure/  # Infrastructure layer: provides technical implementation
│   ├── core/            # Core configuration (config.py)
│   └── main.py          # Application entry
├── Dockerfile           # Docker configuration file
├── pyproject.toml       # Project dependencies and metadata
└── README.md            # Project documentation
```

## Core Features

1. **Session Management**: Create and manage conversation session instances
2. **Real-time Conversation**: Implement real-time conversation through Server-Sent Events (SSE)
3. **Tool Invocation**: Support for various tool calls, including:
   - Browser automation operations (using Playwright)
   - Shell command execution and viewing
   - File read/write operations
   - Web search integration
4. **Sandbox Environment**: Use Docker containers to provide isolated execution environments
5. **VNC Visualization**: Support remote viewing of the sandbox environment via WebSocket connection
6. **Claw (Manus × Claw)**: Per-user OpenClaw container lifecycle management, chat history merge (MongoDB + OpenClaw `.jsonl` sessions), WebSocket real-time messaging, file upload/resolve, and OpenAI-compatible LLM proxy for Claw containers

## Requirements

- Python 3.12+
- Docker 20.10+
- MongoDB 4.4+
- Redis 6.0+

## Installation and Configuration

1. **Install uv**:
```bash
pip install uv
```

2. **Install dependencies**:
```bash
uv sync
```

3. **Environment variable configuration**:
Create a `.env` file and set the following environment variables (see `app/core/config.py` or the root [.env.example](https://github.com/simpleyyt/ai-manus/blob/main/.env.example) for the full list):
```
# Model provider configuration
API_KEY=your_api_key_here                # API key for model providers (required)
API_BASE=https://api.openai.com/v1       # Base URL for model API (optional for some providers)

# Model configuration
MODEL_NAME=gpt-4o                        # Model name to use
MODEL_PROVIDER=openai                    # Model provider for LangChain
LLM_PROVIDER=langchain                   # LLM gateway: langchain (default) or openai (OpenAI SDK)
TEMPERATURE=0.7                          # Model temperature parameter
MAX_TOKENS=2000                          # Maximum output tokens per model request

# Search engine configuration
SEARCH_PROVIDER=bing_web                 # baidu / baidu_web / google / bing / bing_web / tavily / serper / custom
GOOGLE_SEARCH_API_KEY=                   # Google Search API key (SEARCH_PROVIDER=google)
GOOGLE_SEARCH_ENGINE_ID=                 # Google custom search engine ID (SEARCH_PROVIDER=google)

# Sandbox configuration
SANDBOX_ADDRESS=                         # Fixed sandbox address (dev); when unset, containers are created per session
SANDBOX_IMAGE=simpleyyt/manus-sandbox    # Sandbox environment Docker image
SANDBOX_NAME_PREFIX=sandbox              # Sandbox container name prefix
SANDBOX_TTL_MINUTES=30                   # Sandbox container time-to-live (minutes)
SANDBOX_NETWORK=manus-network            # Docker network name for communication between sandbox containers

# Authentication configuration
AUTH_PROVIDER=password                   # password / local / none
JWT_SECRET_KEY=your-secret-key-here      # JWT signing key (set in production)

# Claw (OpenClaw) configuration
CLAW_ENABLED=false                       # Enable the Claw integration
CLAW_IMAGE=simpleyyt/manus-claw          # Claw container Docker image
CLAW_TTL_SECONDS=3600                    # Claw container time-to-live (seconds)

# MCP configuration
MCP_CONFIG_PATH=/etc/mcp.json            # Path to external MCP servers config

# Task backend configuration
TASK_BACKEND=local                       # local (in-process asyncio) or celery (distributed workers)

# Database configuration
MONGODB_URI=mongodb://localhost:27017    # MongoDB connection URL
MONGODB_DATABASE=manus                   # MongoDB database name
REDIS_HOST=localhost                     # Redis host
REDIS_PORT=6379                          # Redis port
REDIS_DB=0                               # Redis DB index

# Log configuration
LOG_LEVEL=INFO                           # Log level, options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Running the Service

### Development Environment
```bash
# Start the development server (with hot reload)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will start at http://localhost:8000.

### Docker Deployment
```bash
# Build Docker image
docker build -t manus-ai-agent .

# Run container
docker run -p 8000:8000 --env-file .env -v /var/run/docker.sock:/var/run/docker.sock manus-ai-agent
```

> Note: If using Docker deployment, you need to mount the Docker socket so the backend can create sandbox containers.

## API Documentation

Base URL: `/api/v1`. Interactive Swagger UI is available at `/docs` while the service is running.

All JSON APIs return a unified envelope:
```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

### Session Endpoints (`/api/v1/sessions`)

| Method | Path | Description |
|---|---|---|
| PUT | `/sessions` | Create a new conversation session |
| GET | `/sessions` | List all sessions |
| POST | `/sessions` | Stream session list updates (SSE) |
| GET | `/sessions/{session_id}` | Get session details including event history |
| DELETE | `/sessions/{session_id}` | Delete a session |
| POST | `/sessions/{session_id}/stop` | Stop an active session |
| POST | `/sessions/{session_id}/chat` | Send a message and receive an SSE event stream |
| POST | `/sessions/{session_id}/clear_unread_message_count` | Clear the unread message count |
| POST | `/sessions/{session_id}/shell` | View shell session output in the sandbox |
| POST | `/sessions/{session_id}/file` | View file content in the sandbox |
| GET | `/sessions/{session_id}/files` | List files attached to the session |
| WebSocket | `/sessions/{session_id}/vnc` | VNC connection to the sandbox (binary subprotocol) |
| POST | `/sessions/{session_id}/vnc/signed-url` | Generate a signed URL for VNC WebSocket access |
| POST | `/sessions/{session_id}/share` | Share a session publicly |
| DELETE | `/sessions/{session_id}/share` | Unshare a session |
| GET | `/sessions/{session_id}/share/files` | List files of a shared session |
| GET | `/sessions/shared/{session_id}` | Get a shared session (no authentication) |

SSE event types emitted by `/chat`: `message`, `title`, `plan`, `step`, `tool`, `wait`, `error`, `done`.

### File Endpoints (`/api/v1/files`)

| Method | Path | Description |
|---|---|---|
| POST | `/files` | Upload a file |
| GET | `/files/{file_id}` | Download a file (supports signed access token) |
| GET | `/files/{file_id}/download` | Download a file as attachment |
| DELETE | `/files/{file_id}` | Delete a file |
| GET | `/files/{file_id}/info` | Get file metadata |
| POST | `/files/{file_id}/signed-url` | Generate a signed download URL |

### Auth Endpoints (`/api/v1/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Login |
| POST | `/auth/register` | Register a new user |
| GET | `/auth/status` | Get authentication provider status |
| GET | `/auth/me` | Get current user information |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout |
| POST | `/auth/change-password` | Change password |
| POST | `/auth/change-fullname` | Change full name |
| POST | `/auth/send-verification-code` | Send email verification code |
| POST | `/auth/reset-password` | Reset password with verification code |
| GET | `/auth/user/{user_id}` | Get user by ID |
| POST | `/auth/user/{user_id}/activate` | Activate a user |
| POST | `/auth/user/{user_id}/deactivate` | Deactivate a user |

### Claw Endpoints (`/api/v1/claw`)

| Method | Path | Description |
|---|---|---|
| GET | `/claw` | Get the current user's Claw instance |
| POST | `/claw` | Create a Claw instance for the current user |
| DELETE | `/claw` | Delete the current user's Claw instance |
| GET | `/claw/api-key` | Get the per-user API key for the LLM proxy |
| GET | `/claw/history` | Get merged Claw chat history |
| POST | `/claw/upload` | Upload a file from the Claw workspace (Claw API key auth) |
| GET | `/claw/files/{filename}` | Proxy a file download from the Claw workspace |
| GET | `/claw/resolve/{file_id}` | Resolve `manus-file://` metadata (Claw API key auth) |
| GET | `/claw/resolve/{file_id}/download` | Download `manus-file://` content (Claw API key auth) |
| WebSocket | `/claw/ws` | Persistent WebSocket connection for Claw chat |

### Other Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/config/frontend` | Frontend runtime configuration |
| POST | `/v1/chat/completions` | OpenAI-compatible LLM proxy used by Claw containers |

## Error Handling

All APIs return responses in a unified format when errors occur:
```json
{
  "code": 400,
  "msg": "Error description",
  "data": null
}
```

Common error codes:
- `400`: Request parameter error
- `404`: Resource not found
- `500`: Server internal error

## Development Guide

### Adding New Tools

1. Define the Protocol interface in the `domain/external` directory
2. Implement the functionality in the `infrastructure/external` layer
3. Wire the implementation in `interfaces/dependencies.py`
4. Expose it as a toolkit in `domain/services/tools` if the agent should call it