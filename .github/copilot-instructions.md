# AI Manus - Copilot Coding Agent Instructions

## Repository Overview

AI Manus is a general-purpose AI Agent system with sandbox environment support. It's a full-stack application comprising three main components:
- **Frontend**: Vue 3 + TypeScript + Vite web application
- **Backend**: FastAPI Python service with Domain-Driven Design (DDD) architecture
- **Sandbox**: Ubuntu-based Docker environment with browser automation capabilities

**Repository Size**: ~600KB source code (excluding node_modules and build artifacts)
**Primary Languages**: Python (backend/sandbox), TypeScript/Vue (frontend)
**Target Runtime**: Docker 20.10+, Docker Compose
**Key Frameworks**: FastAPI, Vue 3, Playwright, MongoDB, Redis

## Critical Build & Development Information

### Environment Requirements
- **Docker**: Version 20.10+ required
- **Docker Compose**: Modern compose (v2) or docker-compose (v1) - auto-detected by scripts
- **Python**: 3.12 (backend), 3.10 (sandbox)
- **Node.js**: 20.18.0 (sandbox), 18+ (frontend)
- **System Access**: Must have access to `/var/run/docker.sock` for sandbox creation

### Initial Setup (ALWAYS DO THIS FIRST)

1. **Create .env file** (REQUIRED before any docker operations):
   ```bash
   cp .env.example .env
   ```
   The `.env` file contains essential configuration for API keys, model settings, and sandbox configuration. Without it, the development environment will not start properly.

2. **Pull pre-built images** (RECOMMENDED for faster development):
   ```bash
   docker pull simpleyyt/manus-frontend
   docker pull simpleyyt/manus-backend
   docker pull simpleyyt/manus-sandbox
   ```

### Build Commands

**IMPORTANT BUILD NOTE**: The Dockerfiles contain Chinese Aliyun mirrors (mirrors.aliyun.com) for faster builds in China. These may fail or be slow outside China. If builds fail due to mirror issues, you may need to modify Dockerfiles to use default repositories.

#### Development Build
```bash
./dev.sh build
```
- Builds all three services (frontend-dev, backend, sandbox, mockserver) using docker-compose-development.yml
- This can take **10-15 minutes** for first build
- Known Issue: Sandbox build may fail if Aliyun mirrors are unreachable

#### Production Build
```bash
./build.sh
```
- Uses `docker buildx bake` command
- Builds production-ready images
- Environment variables:
  - `IMAGE_REGISTRY`: Target registry URL
  - `IMAGE_TAG`: Tag for built images (default: latest)
  - `BUILDX_NO_DEFAULT_ATTESTATIONS=1`: Set automatically

### Running the Application

#### Development Mode (with hot reload)
```bash
./dev.sh up
```
- Starts all services: frontend-dev, backend, sandbox, mockserver, mongodb, redis
- **Frontend** (port 5173): Vue dev server with Vite hot reload
- **Backend** (port 8000): FastAPI with uvicorn --reload
- **Sandbox** (port 8080): API service; (port 5902): VNC; (port 9222): Chrome CDP
- **MongoDB** (port 27017): Database
- **Redis**: Session storage
- Code changes auto-reload (volumes mounted to containers)
- **Only ONE sandbox instance runs globally in dev mode**

Stop services:
```bash
./dev.sh down
```

Clean up everything (including volumes):
```bash
./dev.sh down -v
```

Rebuild after dependency changes:
```bash
./dev.sh down -v
./dev.sh build
./dev.sh up
```

#### Production Mode
```bash
./run.sh up -d
```
- Uses docker-compose.yml
- Creates new sandbox containers per session (not shared)

### Testing

#### Backend Tests
Location: `backend/tests/`
Test Framework: pytest with async support

Run tests:
```bash
cd backend
# Install dependencies first (if not in container)
pip install -r requirements.txt
pip install -r tests/requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_agent_service.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

**Test Configuration** (pytest.ini):
- `asyncio_mode = auto`: Automatically handles async tests
- Logs enabled at INFO level
- Tests located in `tests/` directory
- Test file pattern: `test_*.py`

**Important**: Tests mock MCP (Model Context Protocol) modules in conftest.py to avoid import issues.

#### Sandbox Tests
Location: `sandbox/tests/`

Run tests:
```bash
cd sandbox
pip install -r requirements.txt
pytest
```

#### Frontend Tests
No automated tests currently configured in the repository.

### Linting & Code Quality

**Backend**:
- No explicit linter configuration found in repo
- Follow PEP 8 Python style guidelines
- Use type hints (pydantic models used throughout)

**Frontend**:
- TypeScript configured (tsconfig.json, tsconfig.app.json, tsconfig.node.json)
- Run type checking: `npm run type-check`
- Vite build validates types

## Project Architecture

### Directory Structure

```
ai-manus/
├── .github/                    # GitHub configuration
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── domain/            # Domain layer: business logic
│   │   │   ├── models/        # Domain models
│   │   │   ├── services/      # Domain services (agent_task_runner.py, flows/)
│   │   │   ├── external/      # External service interfaces
│   │   │   └── prompts/       # LLM prompt templates
│   │   ├── application/       # Application layer: orchestration
│   │   │   ├── services/      # App services (token_service.py, email_service.py)
│   │   │   └── schemas/       # Data schemas
│   │   ├── interfaces/        # Interface layer: API routes
│   │   │   └── api/routes.py  # Main API route definitions
│   │   ├── infrastructure/    # Infrastructure: technical implementation
│   │   │   └── external/sandbox/docker_sandbox.py
│   │   ├── core/              # Core configuration
│   │   └── main.py            # Application entry point
│   ├── tests/                 # pytest tests
│   ├── pytest.ini             # Pytest configuration
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile
│   ├── dev.sh                 # Dev server: uvicorn with --reload
│   └── run.sh                 # Prod server: uvicorn without reload
├── frontend/                  # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable Vue components
│   │   │   ├── ui/           # UI library components
│   │   │   ├── ChatInput.vue
│   │   │   ├── ChatMessage.vue
│   │   │   ├── Sidebar.vue
│   │   │   └── ToolPanel.vue
│   │   ├── pages/            # Page components
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json          # npm scripts: dev, build, type-check
│   ├── vite.config.ts        # Vite configuration
│   ├── tsconfig.json         # TypeScript config
│   ├── nginx.conf            # Production nginx config
│   └── Dockerfile
├── sandbox/                   # Sandbox execution environment
│   ├── app/
│   │   ├── api/v1/           # API endpoints
│   │   │   ├── shell.py      # Shell command execution
│   │   │   ├── file.py       # File operations
│   │   │   └── supervisor.py # Process management
│   │   ├── services/         # Service implementations
│   │   ├── schemas/          # FastAPI models
│   │   └── main.py
│   ├── tests/                # pytest tests
│   ├── supervisord.conf      # Supervisor process manager config
│   ├── requirements.txt
│   └── Dockerfile
├── mockserver/               # Mock LLM server for testing
├── docs/                     # Documentation (Chinese)
├── .env.example              # Environment template
├── docker-compose.yml        # Production compose file
├── docker-compose-development.yml  # Development compose file
├── dev.sh                    # Development helper script
├── run.sh                    # Production helper script
├── build.sh                  # Build helper (uses docker buildx bake)
└── README.md
```

### Key Configuration Files

#### Backend Configuration
- **app/core/config.py**: Environment variable loading, settings management
- **pytest.ini**: Test configuration (asyncio_mode=auto, log settings)
- **requirements.txt**: 23 dependencies including fastapi, openai, playwright, docker, motor (MongoDB), redis

#### Frontend Configuration
- **vite.config.ts**: Vite build configuration
- **tsconfig.json**: TypeScript compilation settings
- **package.json**: Scripts: dev (vite), build (vite build), type-check (vue-tsc)
- **nginx.conf**: Production server configuration

#### Sandbox Configuration
- **supervisord.conf**: Manages Chrome, x11vnc, websockify, uvicorn processes
- **UVI_ARGS** env var: Pass args to uvicorn (e.g., "--reload" in dev)
- **CHROME_ARGS** env var: Pass args to Chrome browser

### Docker Compose Services

#### Development (docker-compose-development.yml)
- **frontend-dev**: Vite dev server, port 5173, hot reload enabled
- **backend**: FastAPI with reload, port 8000, mounts /var/run/docker.sock
- **sandbox**: Single shared instance, ports 8080/5902, hot reload enabled
- **mockserver**: Mock LLM API for testing
- **mongodb**: Port 27017
- **redis**: Default port
- **Network**: manus-network (bridge driver)

#### Production (docker-compose.yml)
- Uses pre-built images from Docker Hub (simpleyyt/manus-*)
- Backend creates sandbox containers dynamically per session
- No port exposure for MongoDB/Redis (internal only)

### API Endpoints

**Backend Base URL**: `http://localhost:8000/api/v1`

Key endpoints:
- `PUT /sessions` - Create new session
- `GET /sessions` - List sessions
- `GET /sessions/{id}` - Get session details
- `DELETE /sessions/{id}` - Delete session
- `POST /sessions/{id}/chat` - Send message (SSE streaming response)
- `POST /sessions/{id}/stop` - Stop session
- `POST /sessions/{id}/shell` - View shell output
- `POST /sessions/{id}/file` - View file content
- `WebSocket /sessions/{id}/vnc` - VNC connection

**Sandbox Base URL**: `http://localhost:8080/api/v1`

Key endpoints:
- Shell: `/shell/exec`, `/shell/view`, `/shell/wait`, `/shell/write`, `/shell/kill`
- File: `/file/read`, `/file/write`, `/file/replace`, `/file/search`, `/file/find`
- Supervisor: `/supervisor/status`, `/supervisor/stop`, `/supervisor/restart`, `/supervisor/timeout/*`

## Environment Variables & Configuration

**Critical Variables** (must be set in .env):
- `API_KEY`: LLM API key (required)
- `API_BASE`: LLM API endpoint (default: http://mockserver:8090/v1)
- `MODEL_NAME`: Model to use (default: deepseek-chat)
- `SANDBOX_IMAGE`: Docker image for sandbox (default: simpleyyt/manus-sandbox)
- `SANDBOX_NETWORK`: Docker network name (default: manus-network)
- `JWT_SECRET_KEY`: JWT signing key (default: your-secret-key-here - **CHANGE IN PRODUCTION**)

**Optional but Important**:
- `MONGODB_URI`, `MONGODB_DATABASE`: Database connection (commented out = optional)
- `REDIS_HOST`, `REDIS_PORT`: Session storage (commented out = optional)
- `AUTH_PROVIDER`: Authentication mode (password/none/local, default: password)
- `SEARCH_PROVIDER`: Search engine (baidu/google/bing, default: bing)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Common Development Patterns

### Making Backend Changes
1. Edit code in `backend/app/`
2. Changes auto-reload (uvicorn --reload in dev mode)
3. Check logs: `./dev.sh logs backend`
4. Run tests: `cd backend && pytest`

### Making Frontend Changes
1. Edit code in `frontend/src/`
2. Vite hot-reloads automatically
3. Check browser console and terminal for errors
4. Type check: `cd frontend && npm run type-check`

### Making Sandbox Changes
1. Edit code in `sandbox/app/`
2. Changes auto-reload in dev mode
3. Test API: `curl http://localhost:8080/api/v1/supervisor/status`

### Adding Python Dependencies
1. Add to `backend/requirements.txt` or `sandbox/requirements.txt`
2. Rebuild container: `./dev.sh down -v && ./dev.sh build && ./dev.sh up`

### Adding Frontend Dependencies
1. Add to `frontend/package.json` or run `npm install <package>` locally
2. Rebuild container: `./dev.sh down -v && ./dev.sh build && ./dev.sh up`

## Known Issues & Workarounds

### Build Issues
1. **Aliyun mirror failures**: Dockerfiles use Chinese mirrors (mirrors.aliyun.com). If unreachable:
   - Edit `sandbox/Dockerfile` lines 9-12 to use default Ubuntu repos
   - Edit `backend/Dockerfile` line 28 to remove `UV_INDEX_URL`
   - Edit `sandbox/Dockerfile` lines 44, 56 to remove mirror configs

2. **SSL certificate errors during build**: Network/proxy issues. Retry or check proxy settings.

### Runtime Issues
1. **"sandbox-1 exited with code 0"**: NORMAL in production mode - ensures image is pulled
2. **Docker socket permission denied**: Ensure user is in docker group or run with sudo
3. **Port already in use**: Check if services are already running: `./dev.sh down`

### Code Patterns to Note
- TODO comments exist in codebase (see backend/app/domain/services/agent_task_runner.py, docker_sandbox.py)
- Don't remove or modify these without understanding context

## Testing Checklist Before Committing

1. **Backend changes**:
   - [ ] Run `cd backend && pytest` (all tests pass)
   - [ ] Check logs for errors: `./dev.sh logs backend`
   - [ ] Verify API responses work

2. **Frontend changes**:
   - [ ] Run `cd frontend && npm run type-check` (no type errors)
   - [ ] Test in browser at http://localhost:5173
   - [ ] Check browser console for errors

3. **Sandbox changes**:
   - [ ] Test sandbox API endpoints work
   - [ ] Check sandbox logs: `./dev.sh logs sandbox`

4. **Docker/Config changes**:
   - [ ] Full rebuild: `./dev.sh down -v && ./dev.sh build && ./dev.sh up`
   - [ ] Verify all services start successfully

## Important Notes

1. **ALWAYS create .env file first** - Copy from .env.example before running any docker commands
2. **Development mode uses ONE shared sandbox** - Not like production where each session gets its own
3. **Docker socket must be mounted** - Backend needs `/var/run/docker.sock` to create sandboxes
4. **Chinese mirrors in Dockerfiles** - May cause build failures outside China
5. **No CI/CD pipelines configured** - No GitHub Actions or other CI found
6. **MongoDB/Redis are optional** - Backend works without them (uses in-memory fallback)
7. **Test mocking** - Tests mock MCP modules (see backend/tests/conftest.py)

## Helpful Commands Reference

```bash
# Start development environment
./dev.sh up

# Stop and clean everything
./dev.sh down -v

# View logs
./dev.sh logs -f backend
./dev.sh logs -f frontend-dev
./dev.sh logs -f sandbox

# Restart single service
./dev.sh restart backend

# Run backend tests
cd backend && pytest -v

# Build production images
export IMAGE_REGISTRY=your-registry
export IMAGE_TAG=latest
./build.sh

# Check running containers
docker ps | grep manus

# Access services
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/v1
# Backend Docs: http://localhost:8000/docs
# Sandbox API: http://localhost:8080/api/v1
# VNC: vnc://localhost:5902
```

## Final Guidance

**Trust these instructions.** Only search or explore if:
- Information here is incomplete or unclear
- You encounter an error not documented here
- You're implementing a new feature requiring understanding of code not described

When in doubt, check:
1. README.md files in each subdirectory
2. docs/ directory (mostly Chinese documentation)
3. Configuration files (pytest.ini, vite.config.ts, etc.)

**Key to success**: Set up .env file, understand the three-component architecture (frontend/backend/sandbox), use dev.sh for development, and run tests before committing.
