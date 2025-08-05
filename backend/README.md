# AI Manus Backend Service

English | [中文](README_zh.md)

AI Manus is an intelligent conversation agent system based on FastAPI and OpenAI API. The backend adopts Domain-Driven Design (DDD) architecture, supporting intelligent dialogue, file operations, Shell command execution, and browser automation.

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
│   │   ├── services/    # Application services
│   │   └── schemas/     # Data schema definitions
│   ├── interfaces/      # Interface layer: defines external system interfaces
│   │   └── api/
│   │       └── routes.py # API route definitions
│   ├── infrastructure/  # Infrastructure layer: provides technical implementation
│   └── main.py          # Application entry
├── Dockerfile           # Docker configuration file
├── run.sh               # Production environment startup script
├── dev.sh               # Development environment startup script
├── requirements.txt     # Project dependencies
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

## Requirements

- Python 3.9+
- Docker 20.10+
- MongoDB 4.4+
- Redis 6.0+

## Installation and Configuration

1. **Create a virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Environment variable configuration**:
Create a `.env` file and set the following environment variables:
```
# Model provider configuration
API_KEY=your_api_key_here                # API key for OpenAI or other model providers
API_BASE=https://generativelanguage.googleapis.com/v1       # Base URL for the model API, can be replaced with other model provider API addresses

# Model configuration
MODEL_NAME=gpt-4o                        # Model name to use
TEMPERATURE=0.7                          # Model temperature parameter
MAX_TOKENS=2000                          # Maximum output tokens per model request

# Google search configuration
GOOGLE_SEARCH_API_KEY=                   # Google Search API key for web search functionality (optional)
GOOGLE_SEARCH_ENGINE_ID=                 # Google custom search engine ID (optional)

# Sandbox configuration
SANDBOX_IMAGE=simpleyyt/manus-sandbox          # Sandbox environment Docker image
SANDBOX_NAME_PREFIX=sandbox              # Sandbox container name prefix
SANDBOX_TTL_MINUTES=30                   # Sandbox container time-to-live (minutes)
SANDBOX_NETWORK=manus-network            # Docker network name for communication between sandbox containers

# Database configuration
MONGODB_URL=mongodb://localhost:27017    # MongoDB connection URL
MONGODB_DATABASE=manus                   # MongoDB database name
REDIS_URL=redis://localhost:6379/0       # Redis connection URL

# Log configuration
LOG_LEVEL=INFO                           # Log level, options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Running the Service

### Development Environment
```bash
# Start the development server (with hot reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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

Base URL: `/api/v1`

### 1. Create Session

- **Endpoint**: `PUT /api/v1/sessions`
- **Description**: Create a new conversation session
- **Request Body**: None
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "session_id": "string"
    }
  }
  ```

### 2. Get Session

- **Endpoint**: `GET /api/v1/sessions/{session_id}`
- **Description**: Get session information including conversation history
- **Path Parameters**:
  - `session_id`: Session ID
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "session_id": "string",
      "title": "string",
      "events": []
    }
  }
  ```

### 3. List All Sessions

- **Endpoint**: `GET /api/v1/sessions`
- **Description**: Get list of all sessions
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "sessions": [
        {
          "session_id": "string",
          "title": "string",
          "latest_message": "string",
          "latest_message_at": 1234567890,
          "status": "string",
          "unread_message_count": 0
        }
      ]
    }
  }
  ```

### 4. Delete Session

- **Endpoint**: `DELETE /api/v1/sessions/{session_id}`
- **Description**: Delete a session
- **Path Parameters**:
  - `session_id`: Session ID
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": null
  }
  ```

### 5. Stop Session

- **Endpoint**: `POST /api/v1/sessions/{session_id}/stop`
- **Description**: Stop an active session
- **Path Parameters**:
  - `session_id`: Session ID
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": null
  }
  ```

### 6. Chat with Session

- **Endpoint**: `POST /api/v1/sessions/{session_id}/chat`
- **Description**: Send a message to the session and receive streaming response
- **Path Parameters**:
  - `session_id`: Session ID
- **Request Body**:
  ```json
  {
    "message": "User message content",
    "timestamp": 1234567890,
    "event_id": "optional event ID"
  }
  ```
- **Response**: Server-Sent Events (SSE) stream
- **Event Types**:
  - `message`: Text message from assistant
  - `title`: Session title update
  - `plan`: Execution plan with steps
  - `step`: Step status update
  - `tool`: Tool invocation information
  - `error`: Error information
  - `done`: Conversation completion

### 7. View Shell Session Content

- **Endpoint**: `POST /api/v1/sessions/{session_id}/shell`
- **Description**: View shell session output in the sandbox environment
- **Path Parameters**:
  - `session_id`: Session ID
- **Request Body**:
  ```json
  {
    "session_id": "shell session ID"
  }
  ```
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "output": "shell output content",
      "session_id": "shell session ID",
      "console": [
        {
          "ps1": "prompt string",
          "command": "executed command",
          "output": "command output"
        }
      ]
    }
  }
  ```

### 8. View File Content

- **Endpoint**: `POST /api/v1/sessions/{session_id}/file`
- **Description**: View file content in the sandbox environment
- **Path Parameters**:
  - `session_id`: Session ID
- **Request Body**:
  ```json
  {
    "file": "file path"
  }
  ```
- **Response**:
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "content": "file content",
      "file": "file path"
    }
  }
  ```

### 9. VNC Connection

- **Endpoint**: `WebSocket /api/v1/sessions/{session_id}/vnc`
- **Description**: Establish a VNC WebSocket connection to the session's sandbox environment
- **Path Parameters**:
  - `session_id`: Session ID
- **Protocol**: WebSocket (binary mode)
- **Subprotocol**: `binary`

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

1. Define the tool interface in the `domain/external` directory
2. Implement the tool functionality in the `infrastructure` layer
3. Integrate the tool in `application/services` 