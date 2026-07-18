# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> A more detailed companion guide lives in [AGENTS.md](AGENTS.md) (env var tables, per-change testing matrix, Cursor Cloud notes). The Cursor starter skill at `.cursor/skills/starter.md` has the full API reference. Read those when you need depth; this file is the orientation.

## What this is

AI Manus is a general-purpose AI Agent system. A user message drives a **plan-and-execute agent loop** in the backend, which runs tools (shell, browser, file, search, MCP) inside a **per-session Docker sandbox** and streams every event back to the browser over **SSE**. The repo is a monorepo of five cooperating services:

| Service | Stack | Dev Port | Entry Point |
|---|---|---|---|
| `frontend` | Vue 3 + TS, Vite, Tailwind, reka-ui | 5173 | `frontend/src/main.ts` |
| `backend` | Python 3.12, FastAPI, LangChain, Beanie/Motor | 8000 (debugpy 5678) | `backend/app/main.py` |
| `sandbox` | Python 3.10, FastAPI + Xvfb/Chrome/VNC under supervisord | 8080 API, 5900 VNC, 9222 CDP | `sandbox/app/main.py` |
| `claw` | Node.js, OpenClaw Gateway + `manus-claw` plugin | 18788 | `claw/entrypoint.sh` |
| `mockserver` | Python, FastAPI (canned LLM responses) | 8090 | `mockserver/main.py` |

Backing services: MongoDB 7.0 (sessions, agents, users) and Redis 7.0 (cache + message queues). The backend talks to `/var/run/docker.sock` to spawn sandbox and Claw containers.

## Commands

Everything runs through Docker Compose wrappers. `./dev.sh` = `docker compose -f docker-compose-development.yml`; `./run.sh` = production compose; `./build.sh` = `docker buildx bake`.

```bash
cp .env.example .env          # then set API_KEY to any non-empty string
./dev.sh up -d                # full hot-reload dev stack
./dev.sh logs -f backend      # tail a service
./dev.sh down -v              # stop + wipe volumes (rebuild after dependency changes)
./dev.sh build                # rebuild images after backend/pyproject.toml or frontend/package.json change
```

> In dev mode only **one** global sandbox container is started (set via `SANDBOX_ADDRESS=sandbox`).

### Testing

Backend and sandbox tests are **integration-style**: they hit a *running* server, so bring the stack up first.

```bash
# Backend (tests in backend/tests/ hit http://localhost:8000)
./dev.sh up -d mongodb redis backend
cd backend && uv run pytest                            # all
cd backend && uv run pytest tests/test_auth_routes.py  # single file
cd backend && uv run pytest -m file_api                # by marker (see backend/pytest.ini)

# Sandbox
./dev.sh up -d sandbox
cd sandbox && uv run pytest

# Frontend — Vitest unit tests + type-check + lint + build
cd frontend && npm run test && npm run type-check && npm run lint && npm run build
```

### Running a service outside Docker

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000   # needs MongoDB+Redis+API_KEY
cd frontend && npm install && BACKEND_URL=http://localhost:8000 npm run dev  # BACKEND_URL enables the /api proxy
```

## Backend architecture (the part worth understanding)

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

## Sandbox & Claw

- **Sandbox** (`sandbox/app/`) is a thin FastAPI service (`api/v1/{shell,file,supervisor}.py`) running inside an Ubuntu container managed by supervisord (Chrome, Xvfb, x11vnc, websockify, the API). One sandbox is spawned per session in production.
- **Claw** (`claw/`) bridges [OpenClaw](https://github.com/anthropics/openclaw) into Manus via the `manus-claw` plugin, giving per-user isolated containers. Backend integration is under `application/services/claw_service.py` + `infrastructure/external/claw/`. Debug help in `.cursor/skills/debug-claw/SKILL.md`.

## Frontend notes

- Vue 3 Composition API, `<script setup lang="ts">` throughout; path alias `@/` → `src/`.
- API layer in `src/api/` (axios + `@microsoft/fetch-event-source` for SSE consumption); pages in `src/pages/`; reusable logic in `src/composables/`; rich tool renderers in `src/components/toolViews/`.
- i18n via vue-i18n (Chinese + English) in `src/locales/`. Add keys to both locales.

## Conventions & gotchas

- **Backend/sandbox have no linter/formatter** (no Ruff/Black). The frontend has **ESLint** (`cd frontend && npm run lint`, flat config in `frontend/eslint.config.js`); no Prettier. Match the style of surrounding code.
- Backend is **async-first** — route handlers and service methods are `async def`.
- Python deps: **uv** + `pyproject.toml` (PEP 621) per service. Frontend: **npm** + `package.json`.
- Config is centralized in `backend/app/core/config.py` (Pydantic `Settings`, `@lru_cache`d `get_settings()`); env vars come from `.env`. For dev, point `API_BASE` at `http://mockserver:8090/v1` and set `AUTH_PROVIDER=none` to skip both real LLM and login.
- CI (`.github/workflows/docker-build-and-push.yml`) only builds/pushes multi-arch Docker images — it runs **no tests or lint**. Verify changes locally.
- Docs site is Docsify under `docs/`; `.cursor/skills/update-docs/update_doc.sh` (and root `./update_doc.sh` wrapper) sync compose/env embeds and README demos (not `docs/demo.md` scenario pages). See `.cursor/skills/update-docs/SKILL.md`.
