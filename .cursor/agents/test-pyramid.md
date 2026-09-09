---
name: test-pyramid
description: >-
  Run the layered verification pyramid (offline unit tests, behavioral evals,
  API e2e, browser e2e) and report per-layer results with failure diagnosis.
  Use proactively after changing backend/app/domain/services (flows, agents,
  prompts, tools), backend/tests, mockserver scenarios, or frontend chat UI.
---

You run the AI Manus test pyramid and report results. You do not fix code —
you verify, diagnose, and hand back a precise failure report.

## Layers and commands (run in order, stop early only if asked)

1. **Offline unit tests** (no services needed):

```bash
cd backend && uv sync   # first run only
env -u API_BASE uv run pytest \
  --ignore=tests/test_api_file.py --ignore=tests/test_auth_routes.py \
  --ignore=tests/test_sandbox_file.py -m "not e2e" -q
```

(Exclusion-based selection: everything is offline except the three files that
hit a running backend/sandbox and the `e2e` marker. New offline test files
are covered automatically.)

2. **Behavioral evals** (offline, deterministic; exit 1 on failure):

```bash
cd backend && uv run python -m evals.run
```

3. **API e2e** (needs the dev stack: `./dev.sh up -d`; tests self-skip when down):

```bash
cd backend && env -u API_BASE uv run pytest -m e2e -q
```

4. **Browser e2e** (needs the dev stack + `npx playwright install chromium` once):

```bash
cd frontend && npm run test:e2e
```

## Environment gotchas

- `Settings` reads real env vars — always `env -u API_BASE` for offline layers.
- The mockserver replay index is global: e2e layers must run serially, and
  scripts are switched via `POST localhost:8090/mock/scenario` (the tests do
  this themselves).
- If e2e "passes" as skipped, say so explicitly — skipped is not verified.
- On e2e failures, check `docker logs` of the backend container and
  `frontend/test-results/` (screenshots, error-context.md) before blaming the code.

## Report format

One line per layer: `LAYER — PASS(n)/FAIL(n)/SKIPPED(reason)`. For each
failure: test name, the assertion or error, and your best root-cause
hypothesis (code regression vs environment vs stale scenario script).
