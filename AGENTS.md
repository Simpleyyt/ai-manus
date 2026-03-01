# AGENTS.md

## Cursor Cloud specific instructions

### Overview
AI Manus is a Docker-based AI Agent system with 6 services: **frontend** (Vue 3/Vite), **backend** (Python/FastAPI), **sandbox** (Ubuntu Docker container with Chromium/VNC), **mockserver** (mock LLM API), **MongoDB**, and **Redis**. All services run as Docker containers via Docker Compose.

### Starting services
```bash
# Start all services in development mode (hot-reload enabled)
./dev.sh up -d

# Check service status
docker compose -f docker-compose-development.yml ps

# View logs
docker compose -f docker-compose-development.yml logs -f <service>
```

### Key ports
- **5173**: Frontend (Vite dev server)
- **8000**: Backend API (`/api/v1/...`)
- **8080**: Sandbox API
- **5902**: Sandbox VNC (mapped from 5900)
- **27017**: MongoDB

### Development configuration
- Copy `.env.example` to `.env` before starting. See README for details.
- The default `.env.example` uses `API_BASE=http://mockserver:8090/v1` (mock LLM), so no real API key is needed for dev/testing.
- Set `AUTH_PROVIDER=local` with `LOCAL_AUTH_EMAIL` / `LOCAL_AUTH_PASSWORD` (min 6 chars) for quick local auth without SMTP.

### Running tests
- **Backend**: `docker compose -f docker-compose-development.yml exec backend python -m pytest tests/`
  - Requires `pytest`, `pytest-asyncio`, `httpx` installed in the container. Many auth tests assume `AUTH_PROVIDER=password` mode and will fail in `local` mode — this is expected.
- **Sandbox**: `docker compose -f docker-compose-development.yml exec sandbox python3 -m pytest tests/`
  - Requires `pytest`, `pytest-asyncio`, `httpx`, `requests` installed in the container.
- **Frontend type-check**: `docker compose -f docker-compose-development.yml exec frontend-dev npm run type-check`
  - Known issue: `vue-tsc` has a compatibility issue with the current TypeScript version; use `npm run build` to verify compilation instead.

### Gotchas
- Docker must be installed and running before `./dev.sh up`. In the Cloud Agent VM, Docker requires fuse-overlayfs storage driver and iptables-legacy.
- The `.env` file is loaded by the backend container via `env_file` in docker-compose. After changing `.env`, run `docker compose -f docker-compose-development.yml up -d` to recreate affected containers (a simple `restart` won't pick up env changes).
- In dev mode, `SANDBOX_ADDRESS=sandbox` is hardcoded in the compose file, so only one sandbox container runs (no dynamic Docker socket sandbox creation).
- The backend container builds its own virtualenv; source code is mounted at `/app` for hot-reload.
