# 🏠 Local Deployment

This guide covers deploying AI Manus on your local machine, from **one-click setup** to **manual configuration**.

## Prerequisites

- **Docker 20.10+** and **Docker Compose**
- An LLM service that supports Function Call (e.g., DeepSeek, OpenAI GPT-4o)
- Recommended: 2+ CPU cores, 4GB+ RAM

### Docker Installation

| System | Installation |
|--------|-------------|
| **Windows / macOS** | Install [Docker Desktop](https://docs.docker.com/desktop/) |
| **Linux** | Install [Docker Engine](https://docs.docker.com/engine/install/) |

## Option 1: One-Click Setup (Recommended)

The project provides a `setup.sh` script with interactive configuration and one-click startup:

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
./setup.sh
```

The script guides you through:
1. **Environment check** — Detects Docker and Docker Compose
2. **LLM configuration** — Set API endpoint, key, and model name
3. **Authentication** — Choose auth mode (local single-user / no auth / password registration)
4. **Search** — Select search engine
5. **Launch** — Pull images and start all services

### Script Options

```bash
./setup.sh                        # Interactive config + pre-built images
./setup.sh --build-from-source    # Interactive config + build from source
./setup.sh --skip-config          # Skip config (use existing .env file)
```

## Option 2: Manual Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
```

### Step 2: Create Configuration File

```bash
cp .env.example .env
```

Edit the `.env` file — at minimum, set these values:

```env
# Required: Set your LLM API key
API_KEY=your-api-key-here

# Required: Set API base URL (varies by provider)
API_BASE=https://api.deepseek.com/v1

# Model name
MODEL_NAME=deepseek-chat

# Recommended: Use local auth for personal use (no registration needed)
AUTH_PROVIDER=local
LOCAL_AUTH_EMAIL=admin@example.com
LOCAL_AUTH_PASSWORD=admin

# Recommended: bing_web search requires no API key
SEARCH_PROVIDER=bing_web
```

> **Security note**: In production, always change `JWT_SECRET_KEY` to a random string.

### Step 3: Start Services

Using pre-built Docker images (recommended, faster):

```bash
docker compose up -d
```

Or build from source:

```bash
docker compose build
docker compose up -d
```

### Step 4: Access the Application

Open your browser and visit http://localhost:5173

> **Note**: If you see `sandbox-1 exited with code 0`, this is normal — it ensures the sandbox image is pulled locally.

## Common Model Configuration Examples

### DeepSeek

```env
API_BASE=https://api.deepseek.com/v1
API_KEY=your-deepseek-key
MODEL_NAME=deepseek-chat
MODEL_PROVIDER=openai
```

### OpenAI

```env
API_BASE=https://api.openai.com/v1
API_KEY=sk-your-openai-key
MODEL_NAME=gpt-4o
MODEL_PROVIDER=openai
```

### Local Ollama

```env
API_BASE=http://host.docker.internal:11434/v1
API_KEY=ollama
MODEL_NAME=qwen2.5:latest
MODEL_PROVIDER=ollama
```

> When using Ollama, ensure the model supports Function Call and JSON format output. `host.docker.internal` is a special hostname for containers to access the host machine. On Linux, you may need to add `--add-host=host.docker.internal:host-gateway` when starting docker compose.

### Other OpenAI-Compatible Services

Any service compatible with the OpenAI API format works — just point `API_BASE` to the right address.

## Authentication Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `local` | Single-user mode with preset email/password | Personal local use (recommended) |
| `none` | No authentication required | Internal testing |
| `password` | Email registration, requires SMTP config | Multi-user production |

## Operations & Management

### Check Service Status

```bash
docker compose ps
```

### View Logs

```bash
docker compose logs -f           # All services
docker compose logs -f backend   # Backend only
```

### Stop Services

```bash
docker compose down
```

### Restart Services

```bash
docker compose restart
```

### Update to Latest Version

```bash
docker compose pull     # Pull latest images
docker compose up -d    # Restart services
```

### Clear All Data

```bash
docker compose down -v  # Stop services and remove volumes
```

> **Warning**: The `-v` flag deletes the MongoDB data volume — all session history will be lost.

## FAQ

### 1. Why did sandbox-1 exit?

`sandbox-1 exited with code 0` is expected behavior. The sandbox service in the compose file exists to pre-pull the sandbox image locally. The backend dynamically creates new sandbox containers per task.

### 2. How to change the port?

Edit `docker-compose.yml` and modify the frontend port mapping:

```yaml
frontend:
  ports:
    - "8080:80"  # Change 5173 to your desired port
```

### 3. How to use custom MCP tools?

1. Create an `mcp.json` configuration file
2. Uncomment the MCP volume mount in `docker-compose.yml`:
   ```yaml
   backend:
     volumes:
       - ./mcp.json:/etc/mcp.json
   ```
3. Restart services

See [MCP Configuration](/en/mcp.md) for details.

### 4. How to configure a proxy?

Set proxy variables in `.env`:

```env
SANDBOX_HTTPS_PROXY=http://your-proxy:port
SANDBOX_HTTP_PROXY=http://your-proxy:port
SANDBOX_NO_PROXY=localhost,127.0.0.1
```

### 5. How to build from source?

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
cp .env.example .env
# Edit .env configuration
docker compose build
docker compose up -d
```

Or use the one-click script:

```bash
./setup.sh --build-from-source
```
