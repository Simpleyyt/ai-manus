# AGENTS.md

> Canonical guide for AI coding agents working on the **AI Manus × Claw** codebase.

---

## Project Overview

AI Manus × Claw is a general-purpose AI Agent system with an integrated [OpenClaw](https://github.com/anthropics/openclaw) AI assistant. A user message drives a **plan-and-execute agent loop** in the backend, which runs tools (shell, browser, file, search, MCP) inside a **per-session Docker sandbox** and streams every event back to the browser over **SSE**. It is a monorepo of five cooperating services:

| Service | Stack | Port (dev) | Entry Point |
|---|---|---|---|
| **Frontend** | Vue 3 + TypeScript, Vite 4, Tailwind CSS, reka-ui | 5173 | `frontend/src/main.ts` |
| **Backend** | Python 3.12, FastAPI, LangChain, Beanie/Motor | 8000 (debugpy 5678) | `backend/app/main.py` |
| **Sandbox** | Python 3.10, FastAPI, Xvfb/Chrome/VNC under supervisord | 8080 (API), 5900 (VNC), 9222 (CDP) | `sandbox/app/main.py` |
| **Claw** | Node.js, OpenClaw Gateway, manus-claw plugin | 18788 | `claw/entrypoint.sh` |
| **Mockserver** | Python, FastAPI (canned LLM responses) | 8090 | `mockserver/main.py` |

Infrastructure: **MongoDB 7.0** (sessions, agents, users), **Redis 7.0** (cache + message queues), **Docker** (sandbox & Claw orchestration). The backend talks to `/var/run/docker.sock` to spawn sandbox and Claw containers.

---

## Directory Structure

```
ai-manus/
├── frontend/          # Vue 3 SPA (Vite, TypeScript, Tailwind)
├── backend/           # FastAPI backend (DDD layout)
│   └── app/
│       ├── domain/           # Models, services, tools, agents, repositories
│       ├── application/      # Application services (auth, agent, file, token, email, claw)
│       ├── infrastructure/   # External integrations (search, browser, sandbox, claw, DB, cache)
│       ├── interfaces/       # API routes, schemas, error handlers, dependencies
│       ├── core/             # Config (config.py)
│       └── main.py
├── sandbox/           # Sandbox service (shell, file, supervisor APIs)
├── claw/              # Claw service (OpenClaw Gateway + manus-claw plugin)
│   └── manus-claw/   # Node.js plugin bridging OpenClaw with Manus backend
├── mockserver/        # Mock LLM server for dev/testing
├── docs/              # Docsify documentation site
├── .cursor/skills/    # Cursor agent skills
├── dev.sh             # Shortcut: docker compose -f docker-compose-development.yml ...
├── run.sh             # Shortcut: docker compose -f docker-compose.yml ...
├── build.sh           # docker buildx bake
├── .env.example       # Environment variable template
├── docker-compose.yml                # Production compose
└── docker-compose-development.yml    # Development compose (hot-reload)
```

---

## Architecture

### Backend (the part worth understanding)

The backend follows **Domain-Driven Design** with strict layer dependencies pointing inward: `interfaces/` → `application/` → `domain/` ← `infrastructure/`.

- **`domain/`** — pure business logic, no framework/IO. The `domain/external/` files are **Protocol interfaces** (`Sandbox`, `Browser`, `LLM`, `SearchEngine`, `FileStorage`, `Task`, `Cache`, `MessageQueue`); concrete implementations live in `infrastructure/external/`. When adding a capability, define the Protocol in `domain/external/` first, implement it in `infrastructure/`, and wire it in `interfaces/dependencies.py`.
- **`application/services/`** — orchestrators (`agent_service`, `auth_service`, `file_service`, `token_service`, `email_service`, `claw_service`) that the API layer calls.
- **`infrastructure/`** — Beanie ODM documents (`infrastructure/models/documents.py`), Mongo/Redis repositories, and the concrete externals (e.g. `external/sandbox/docker_sandbox.py`, `external/browser`, `external/search`, `external/claw`).
- **`interfaces/`** — FastAPI routers (`api/*_routes.py`), Pydantic request/response schemas, error handlers, and `dependencies.py` (the manual DI container — this is where everything is composed).

### The agent loop

This is the heart of the system; understanding it requires reading several files together:

1. **`domain/services/flows/plan_act.py`** — `PlanActFlow.run()` is a state machine: `IDLE → PLANNING → EXECUTING → UPDATING → (repeat) → SUMMARIZING → COMPLETED`. It constructs the toolkit list (Shell, Browser, File, Message, MCP, optional Search) and drives two agents.
2. **`domain/services/agents/`** — `PlannerAgent` (`planner.py`) creates/updates the plan; `ExecutionAgent` (`execution.py`) runs each step. Both extend `BaseAgent` (`base.py`), which wraps LangChain's `init_chat_model`, handles tool-call parsing with retry/repair (`domain/utils/robust_json_parser.py`), memory compaction, and iteration limits.
3. **`domain/services/agent_task_runner.py`** — `AgentTaskRunner` runs the flow as a cancellable background `Task`, so sessions can be stopped/resumed. `AgentDomainService` (`agent_domain_service.py`) coordinates: it lazily creates a sandbox per session (`session.sandbox_id`) and manages task lifecycle.
4. **Events & streaming** — every step yields typed events (`domain/models/event.py`: `PlanEvent`, `MessageEvent`, `ToolEvent`, `TitleEvent`, `DoneEvent`, `WaitEvent`, …). These flow through Redis message queues out to the frontend as **SSE**. Tool output content types (`FileToolContent`, `ShellToolContent`, `BrowserToolContent`, …) let the UI render rich tool views.

Session state lives in MongoDB; `SessionStatus` (`PENDING`/`RUNNING`/`WAITING`/etc.) is what lets the flow resume or roll back a message on reconnect.

### Tools

Each toolkit in `domain/services/tools/` (shell, browser, file, search, message, mcp) extends `BaseToolkit` and exposes methods decorated as `Tool`s. Shell/file tools call the **sandbox** API; browser tools drive the sandbox's headless Chrome (viewable via VNC→websockify→NoVNC); `mcp.py` loads external MCP servers from a mounted `mcp.json` (see `mcp.json.example`).

### Sandbox & Claw

- **Sandbox** (`sandbox/app/`) is a thin FastAPI service (`api/v1/{shell,file,supervisor}.py`) running inside an Ubuntu container managed by supervisord (Chrome, Xvfb, x11vnc, websockify, the API). One sandbox is spawned per session in production.
- **Claw** (`claw/`) bridges [OpenClaw](https://github.com/anthropics/openclaw) into Manus via the `manus-claw` plugin, giving per-user isolated containers. Backend integration is under `application/services/claw_service.py` + `infrastructure/external/claw/`. Debug help in `.cursor/skills/debug-claw/SKILL.md`.

### Frontend

- Vue 3 Composition API, `<script setup lang="ts">` throughout; path alias `@/` → `src/`.
- API layer in `src/api/` (axios + `@microsoft/fetch-event-source` for SSE consumption); pages in `src/pages/`; reusable logic in `src/composables/`; rich tool renderers in `src/components/toolViews/`.
- i18n via vue-i18n (Chinese + English) in `src/locales/`. Add keys to both locales.

---

## Development Environment Setup

### Prerequisites

- **Docker 20.10+** and **Docker Compose**
- **uv** (Python package manager) — for running backend/sandbox outside Docker
- **Node.js / npm** — for running frontend outside Docker
- **Python 3.12+** (backend), **Python 3.10+** (sandbox)

### Quick Start (Docker Compose — Recommended)

```bash
cp .env.example .env
# Edit .env — at minimum set API_KEY to any non-empty string
./dev.sh up -d
```

This starts: frontend (5173), backend (8000), sandbox (8080), mockserver (8090), MongoDB (27017), Redis.

### Key `.env` Values for Development

| Variable | Recommended Value | Purpose |
|---|---|---|
| `AUTH_PROVIDER` | `none` | Skip authentication entirely |
| `API_BASE` | `http://mockserver:8090/v1` | Use mock LLM server |
| `API_KEY` | any non-empty string | Required — set to anything with mockserver |
| `SEARCH_PROVIDER` | `bing_web` | No API key needed |
| `SANDBOX_ADDRESS` | `sandbox` | Use single dev sandbox container |
| `LOG_LEVEL` | `DEBUG` | Verbose logging |

### Running Services Individually (Without Docker)

**Backend:**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Requires running MongoDB and Redis. Requires `API_KEY` env var (or `.env` in `backend/`).

**Frontend:**
```bash
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev
```
The Vite config creates a proxy for `/api` when `BACKEND_URL` is set.

**Sandbox:** Typically Docker-only (requires Xvfb, Chrome, VNC, supervisord).

**Mockserver:**
```bash
cd mockserver
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8090 --reload
```

---

## Testing

### Backend Tests (pytest — integration-style)

Tests live in `backend/tests/` and hit a **running** backend at `http://localhost:8000`.

```bash
# Ensure backend + MongoDB + Redis are running
./dev.sh up -d mongodb redis backend

cd backend
uv run pytest                               # all tests
uv run pytest tests/test_auth_routes.py     # specific file
uv run pytest -m file_api                   # by marker
```

Key test files:
- `tests/test_auth_routes.py` — auth endpoints
- `tests/test_api_file.py` — file upload/download
- `tests/test_sandbox_file.py` — sandbox file operations

Config: `backend/pytest.ini` (`asyncio_mode = auto`, markers: `file_api`).

### Sandbox Tests (pytest)

```bash
./dev.sh up -d sandbox
cd sandbox
uv run pytest
```

### Frontend (No Automated Test Runner)

```bash
cd frontend
npm run type-check    # vue-tsc type checking
npm run build         # production build (catches TS + template errors)
```

For manual UI testing: start full dev stack (`./dev.sh up -d`), open `http://localhost:5173`.

### Mockserver

No tests. Verify with:
```bash
curl -X POST http://localhost:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
```

### Full-Stack Integration Test

1. `./dev.sh up -d` — start all services
2. Open `http://localhost:5173`
3. Login (or bypass with `AUTH_PROVIDER=none`)
4. Create session, send message — mockserver returns canned tool calls
5. Check logs: `./dev.sh logs -f backend`
6. Check VNC at `localhost:5902` for sandbox desktop

---

## Code Conventions

### Backend (Python)

- **DDD architecture**: `domain/` → `application/` → `infrastructure/` → `interfaces/`
- **FastAPI** with **Pydantic v2** models and settings
- **Beanie** ODM for MongoDB documents (`infrastructure/models/documents.py`)
- **Redis** for caching and message queues
- Dependency management: **uv** + `pyproject.toml` (PEP 621)
- No enforced linter/formatter (no Ruff, Black, or Flake8 configured)
- Async-first: use `async def` for route handlers and service methods

### Frontend (TypeScript / Vue)

- **Vue 3 Composition API** with `<script setup lang="ts">`
- **TypeScript** throughout
- **Tailwind CSS** for styling, **reka-ui** component library
- Path alias: `@/` → `src/`
- **vue-i18n** for internationalization (Chinese + English)
- Dependency management: **npm** + `package.json`
- No ESLint or Prettier configured

### Sandbox (Python)

- **FastAPI** service exposing shell, file, and supervisor APIs
- Runs inside Docker with **supervisord** managing Chrome, Xvfb, VNC, and the API
- Dependency management: **uv** + `pyproject.toml`

### Gotchas

- Config is centralized in `backend/app/core/config.py` (Pydantic `Settings`, `@lru_cache`d `get_settings()`); env vars come from `.env`. For dev, point `API_BASE` at `http://mockserver:8090/v1` and set `AUTH_PROVIDER=none` to skip both real LLM and login.
- In dev mode only **one** global sandbox container is started (set via `SANDBOX_ADDRESS=sandbox`).
- Docs site is Docsify under `docs/`; `update_doc.sh` and `.cursor/skills/update-docs/SKILL.md` regenerate snippets embedded from compose files.

---

## CI/CD

Single GitHub Actions workflow: `.github/workflows/docker-build-and-push.yml`

- **Triggers**: push/PR to `main` and `develop`; tags `v*`
- **Builds**: matrix of `frontend`, `backend`, `sandbox` Docker images for `linux/amd64` and `linux/arm64`
- **Pushes** to Docker Hub on non-PR events (requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets)
- **No** automated test or lint steps in CI

---

## Cursor Cloud Specific Instructions

### Environment Setup

When running in a Cloud Agent environment:

1. Docker may not be available. If Docker commands fail, focus on running individual services or testing code changes without the full stack.
2. For backend work, install dependencies with `cd backend && uv sync`.
3. For frontend work, install dependencies with `cd frontend && npm install`.
4. Set `AUTH_PROVIDER=none` and `API_KEY=test` in `.env` to bypass auth and LLM requirements.

### Testing Strategy by Change Type

| Change Type | Testing Approach |
|---|---|
| Backend Python logic | `cd backend && uv run pytest` (needs running backend + MongoDB + Redis) |
| Backend API routes | `cd backend && uv run pytest` against running server |
| Frontend Vue/TS | `cd frontend && npm run type-check && npm run build` |
| Frontend UI changes | Type-check + build + manual GUI testing via `computerUse` subagent |
| Sandbox changes | `cd sandbox && uv run pytest` |
| Config / env changes | Verify with `./dev.sh up -d` and check service logs |
| Documentation / README | No testing needed |

### Debugging the Backend

The dev compose starts the backend with **debugpy** on port `5678`. Attach a remote Python debugger for step-through debugging.

### Resetting State

- MongoDB data persists in volume `manus-mongodb-data`. Wipe with `./dev.sh down -v`.
- Mockserver tracks response index; restart to reset: `./dev.sh restart mockserver`.

---

## Skills

| Skill File | When to Use |
|---|---|
| `.cursor/skills/starter.md` | Setting up, running, or testing any part of the codebase. Contains detailed API reference, env var tables, and testing workflows. |
