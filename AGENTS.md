# AGENTS.md

> Canonical guide for AI coding agents working on the **AI Manus** codebase.

---

## Project Overview

AI Manus is a general-purpose AI Agent system, comprising four services:

| Service | Stack | Port (dev) | Entry Point |
|---|---|---|---|
| **Frontend** | Vue 3 + TypeScript, Vite 4, Tailwind CSS | 5173 | `frontend/src/main.ts` |
| **Backend** | Python 3.12, FastAPI, LangChain, Beanie/Motor | 8000 | `backend/app/main.py` |
| **Sandbox** | Python 3.10, FastAPI, Xvfb/Chrome/VNC | 8080 (API), 5900 (VNC) | `sandbox/app/main.py` |
| **Mockserver** | Python, FastAPI | 8090 | `mockserver/main.py` |

Infrastructure: **MongoDB 7.0**, **Redis 7.0**, **Docker** (sandbox orchestration).

---

## Directory Structure

```
ai-manus/
├── frontend/          # Vue 3 SPA (Vite, TypeScript, Tailwind)
├── backend/           # FastAPI backend (DDD layout)
│   └── app/
│       ├── domain/           # Models, services, tools, agents, repositories
│       ├── application/      # Application services (auth, agent, file, token, email)
│       ├── infrastructure/   # External integrations (search, browser, sandbox, DB, cache)
│       ├── interfaces/       # API routes, schemas, error handlers, dependencies
│       ├── core/             # Config (config.py)
│       └── main.py
├── sandbox/           # Sandbox service (shell, file, supervisor APIs)
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

Config: `backend/pytest.ini` (`asyncio_mode = auto`, markers: `file_api`, `e2e`).

### Agent Harness E2E + Evals

```bash
# API e2e over the real stack (self-skips if the stack is down)
./dev.sh up -d
cd backend && uv run pytest -m e2e

# Browser e2e (Playwright drives the real UI at localhost:5173)
cd frontend && npx playwright install chromium   # once
cd frontend && npm run test:e2e

# Offline behavioral evals (deterministic, no services needed; exit 1 on failure)
cd backend && uv run python -m evals.run
```

API e2e (`backend/tests/test_e2e_plan_act.py`) drives the chat WebSocket directly; browser e2e (`frontend/e2e/plan-act.spec.ts`) drives the rendered UI as a user. Both replay mockserver scenarios switched via `POST localhost:8090/mock/scenario`. Evals (`backend/evals/`) score PlanActFlow behavior (completion, LLM-call budget, replans, self-repairs, rejections). See `.cursor/skills/harness/SKILL.md`.

### Sandbox Tests (pytest)

```bash
./dev.sh up -d sandbox
cd sandbox
uv run pytest
```

### Frontend (Vitest)

```bash
cd frontend
npm run test          # Vitest unit tests (src/**/*.spec.ts)
npm run type-check    # vue-tsc type checking
npm run lint          # ESLint (flat config, eslint.config.js)
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

## AI Coding Loop

The standard working loop for AI agents making changes in this repo:

1. **Scope** — identify the change type and read the matching skill first (see Skills table; harness changes → `.cursor/skills/harness/SKILL.md`, UI parity → `replicate-manus-ui`, docs → `update-docs`).
2. **Implement** — follow Code Conventions; match surrounding style; keep layer boundaries (`domain` ← `infrastructure`, wired in `interfaces/dependencies.py`).
3. **Verify** — run the test pyramid for the affected layers (see Testing Strategy by Change Type). Delegate to the `test-pyramid` subagent to run all layers and get a per-layer failure report.
4. **Guard** — for changes under `backend/app/domain/services` or `domain/models`, run the `harness-reviewer` subagent (read-only) to check the diff against harness invariants and required companion updates. For Manus UI parity work, run the `ui-parity-auditor` subagent before claiming a surface is aligned.
5. **Sync** — update companions in the same change: tests (`backend/tests/`, shared fakes in `tests/harness.py`), eval scenarios (`backend/evals/scenarios.py`), skill docs (invariants in the harness skill), and doc embeds via `.cursor/skills/update-docs/update_doc.sh`.
6. **Ship** — one logical change per commit; verify lint/type-check for frontend changes (`npm run type-check && npm run lint`).

### Subagents (`.cursor/agents/`)

| Subagent | Mode | Use |
|---|---|---|
| `test-pyramid` | read/write | Runs all four automated verification layers (unit → evals → API e2e → browser e2e) and reports per-layer results with failure diagnosis. Use after harness/test/scenario/chat-UI changes. |
| `harness-reviewer` | read-only | Reviews a diff against the harness invariants and the companion-update checklist (tests/evals/skill/mock scenarios). Use before committing `domain/services` changes. |
| `ui-parity-auditor` | read-only | Audits Manus-parity frontend changes against mined official class trees and the 直接抄 rules (`replicate-manus-ui` skill). Use before claiming a surface is aligned; mining itself still needs the user's logged-in Chrome. |

Cursor loads these from `.cursor/agents/*.md` (also compatible with `.claude/agents/`). Invoke explicitly with `/test-pyramid` / `/harness-reviewer`, or let the agent delegate automatically.

### Autonomy Stack (unattended-by-design)

**Lifecycle**: every stage from task intake to regression repair is wired so no human sits in the loop:

| Stage | Automation |
|---|---|
| Task intake | **Features**: file an issue with the `Agent task` template (`.github/ISSUE_TEMPLATE/agent-task.yml`, goal + acceptance criteria, auto-labeled `agent-task`) → a Cursor automation on the label (or an `@cursor` comment) dispatches a Cloud Agent, whose PR closes the issue. **Defects**: nightly regressions self-file `autonomy-regression` issues that enter the same dispatch path. Ad-hoc: `@cursor` on any issue/PR, Slack, cursor.com/agents, or the Cloud Agents API |
| Develop | AI Coding Loop (above) + skills; agent commits and opens the PR itself |
| Verify (inner) | L1 `stop` hook — the turn cannot end red |
| Review | L2 guard subagents + platform review bots on the PR |
| Merge gate | L3 CI (`tests.yml`): offline tests + evals, frontend checks, secret scan, docs-drift, full e2e (API + browser + sandbox); branch protection makes green mandatory |
| Dependencies | Dependabot (`.github/dependabot.yml`) opens weekly upgrade PRs for uv (backend/sandbox), npm, pip, Docker base images, and Actions; L3 green + auto-merge lands them unattended |
| Release | `docker-build-and-push.yml` publishes images on merge to `main` and tags (`release` skill covers versioned notes) |
| Watch | `nightly.yml` reruns the full gate on `main` daily; failures open/append the regression issue automatically |

Reproducibility: `backend/uv.lock`, `sandbox/uv.lock` and `frontend/package-lock.json` are committed; CI installs with `uv sync --frozen` / `npm ci`; Dependabot keeps them fresh. Doc embeds are generated (`update_doc.sh`) and drift-gated in CI.

**Remaining human touchpoints** (by design, one-time or judgment-only):
- One-time GitHub setup: branch protection requiring the `Tests` jobs, enabling auto-merge, allowing Actions to create issues; optional Cursor automations for issue → agent dispatch.
- Judgment calls: merging (or enabling auto-merge per PR), product/UX decisions, mining manus.im dumps (needs a logged-in browser), and rotating secrets.

Four gate layers remove the human from the verify-fix loop; each outer layer backstops the inner ones:

| Layer | Mechanism | What it enforces |
|---|---|---|
| L1 — session gate | `.cursor/hooks.json` `stop` hook → `.cursor/hooks/verify_on_stop.py` | The agent cannot end a turn while backend offline tests/evals or frontend unit tests fail for areas touched by **unpushed** work (uncommitted + commits ahead of `@{upstream}`). Once pushed, CI owns verification and the gate passes in milliseconds. Failures come back as an auto follow-up with the failure tail (max 3 loops). Fail-open on missing env — environment problems must not trap the agent. |
| L2 — guard subagents | `.cursor/agents/` (`test-pyramid`, `harness-reviewer`, `ui-parity-auditor`) | Heavy verification (e2e layers) and semantic review (invariants, UI parity) on demand, per the AI Coding Loop. |
| L3 — CI hard gate | `.github/workflows/tests.yml` + `nightly.yml` | Every push/PR to `main`/`develop` runs backend offline tests + evals, frontend unit/type-check/lint/build, gitleaks secret scan, docs-drift, and full-stack e2e (API + browser + sandbox API tests) against the dev compose stack. Nightly reruns it all on `main` and files/updates an `autonomy-regression` issue on failure. |
| L4 — platform | Branch protection + review bots (one-time human setup on GitHub/Cursor) | PRs merge only when L3 is green; automated review comments feed back into agent runs. |

Offline test selection is exclusion-based (`--ignore` the three server-dependent files + `-m "not e2e"`) and must stay in sync across the hook, the `test-pyramid` subagent, and CI.

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
- **ESLint** configured (`npm run lint`); no Prettier
- **Vitest** + @vue/test-utils for unit tests (`npm run test`)

### Sandbox (Python)

- **FastAPI** service exposing shell, file, and supervisor APIs
- Runs inside Docker with **supervisord** managing Chrome, Xvfb, VNC, and the API
- Dependency management: **uv** + `pyproject.toml`

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
| Frontend Vue/TS | `cd frontend && npm run test && npm run type-check && npm run lint && npm run build` |
| Frontend UI changes | Type-check + build + manual GUI testing via `computerUse` subagent |
| Agent harness (`domain/services` flows/agents/prompts/tools) | Offline: `uv run pytest tests/test_plan_act_flow.py tests/test_context_engineering.py tests/test_single_loop_manus.py` + `uv run python -m evals.run`; full stack: `uv run pytest -m e2e` + `cd frontend && npm run test:e2e` |
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
| `.cursor/skills/harness/SKILL.md` | Changing the agent framework (`backend/app/domain/services`: flows, agents, prompts, tools, events). File map, invariants, extension recipes, offline test harness (`backend/tests/harness.py`) and mockserver scenarios. |
| `.cursor/skills/manus-official-cdp/SKILL.md` | Logged-in manus.im over Chrome CDP via Default-profile `session_id` (inject / verify / geo `/unavailable`); use before replicate-manus-ui capture. |
| `.cursor/skills/replicate-manus-ui/SKILL.md` | Align frontend UI with manus.im (mine official JS/DOM; Computer / sidebar / Library / Project / Search / chat chrome parity). |
| `.cursor/skills/update-docs/SKILL.md` | Sync compose/env embeds + README demos via `.cursor/skills/update-docs/update_doc.sh` (not docs/demo.md scenarios). |
| `.cursor/skills/demo-videos/SKILL.md` | Recording/uploading README demo MP4s (`tmp/videos` + `gh image` + `docs/demos.yml`; never commit binaries; publish only after user confirmation). |
| `.cursor/skills/release/SKILL.md` | Cutting `vX.Y.Z` GitHub releases (bilingual notes like v2.4.0/v2.5.0; no demo-videos-* releases). |

Personal (not in repo): `~/.cursor/skills/telegram-screenshots/SKILL.md` — UI screenshots → Telegram Bot MCP.
