# Copilot Coding Agent Instructions for AI Manus

## Overview
AI Manus is a multi-component AI agent system with a backend (FastAPI, DDD), sandbox (Docker-based secure execution), and frontend (Vue 3 + Vite). The architecture is designed for modularity, security, and extensibility, supporting real-time chat, tool invocation, and browser/file/shell automation.

## Architecture & Key Directories
- **backend/app/domain/**: Core business logic, models, services, and external service interfaces
- **backend/app/application/**: Orchestrates business processes, application services, and schemas
- **backend/app/interfaces/api/**: API route definitions (FastAPI)
- **backend/app/infrastructure/**: Technical implementations (DB, logging, config)
- **backend/app/main.py**: Backend entry point
- **sandbox/app/**: Isolated execution (shell, file, browser, VNC), API interfaces, and service implementations
- **frontend/src/**: Vue 3 app, chat UI, tool panels, and API clients

## Developer Workflows
- **Backend (dev):**
  - `cd backend && ./dev.sh` or `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **Backend (prod):**
  - `cd backend && ./run.sh` or use Docker: `docker build -t manus-ai-agent . && docker run ...`
- **Sandbox:**
  - `cd sandbox && ./dev.sh` or run via Docker (see README)
- **Frontend:**
  - `cd frontend && npm install`
  - `npm run dev` (dev mode)
  - `npm run build` (production build)

## Patterns & Conventions
- **Domain-Driven Design (DDD):** Backend is strictly layered (domain, application, interfaces, infrastructure)
- **Tool Invocation:** Backend supports browser, shell, file, and web search tools via API endpoints
- **Sandbox Isolation:** All risky operations (shell, browser) are proxied through the sandbox Docker service
- **Configuration:** Use `.env` files for secrets and service URLs; see backend/README.md for required variables
- **API Versioning:** All backend APIs are under `/api/v1/`
- **Testing:**
  - Backend: `cd backend && pytest`
  - Sandbox: `cd sandbox && pytest`
  - Frontend: Standard Vite/Vue test tools (not included by default)

## Integration Points
- **Backend <-> Sandbox:** Communicate via Docker network and REST APIs; backend launches/manages sandbox containers
- **Frontend <-> Backend:** Uses REST API (`VITE_API_URL` in frontend config)
- **External:** OpenAI API, Google Search API (optional)

## Examples
- Add a new backend tool: implement in `domain/services/`, expose via `interfaces/api/`, wire in `application/services/`
- Add a new frontend panel: create Vue component in `src/components/`, register in `src/pages/`

## References
- See `backend/README.md`, `sandbox/README.md`, and `frontend/README.md` for more details and up-to-date commands.

---
If any section is unclear or missing, please provide feedback for further refinement.
