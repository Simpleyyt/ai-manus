#!/usr/bin/env python3
"""Stop-hook gate: the agent may not finish a turn while cheap offline
verification fails.

Contract (Cursor hooks): read the stop payload from stdin; print JSON to
stdout. A non-empty {"followup_message": ...} re-prompts the agent (bounded
by loop_limit in .cursor/hooks.json); {} lets the turn end.

Scope: only the fast, service-free layers run here — backend offline unit
tests + behavioral evals, frontend unit tests + type-check — and only for
the areas actually touched (vs origin/main + uncommitted work). Heavier
layers (API/browser e2e) stay in CI and the test-pyramid subagent.

Fail-open policy: a missing interpreter/venv/node_modules or a hook crash
must never trap the agent — those are environment problems, not code
problems, and CI still gates the merge.
"""

import json
import os
import subprocess
import sys

ROOT = os.environ.get("CURSOR_PROJECT_DIR", os.getcwd())

# Offline = everything except the files that need a running backend/sandbox
# and the e2e marker. Exclusion keeps new offline tests covered automatically.
# Keep in sync with .cursor/agents/test-pyramid.md and .github/workflows/tests.yml.
OFFLINE_PYTEST_ARGS = [
    "--ignore=tests/test_api_file.py",
    "--ignore=tests/test_auth_routes.py",
    "--ignore=tests/test_sandbox_file.py",
    "-m", "not e2e",
]

BACKEND_PREFIXES = ("backend/", "mockserver/")
FRONTEND_PREFIXES = ("frontend/src/", "frontend/package.json", "frontend/tsconfig")

TAIL = 1500


def sh(args, cwd, env=None, timeout=240):
    return subprocess.run(
        args, cwd=cwd, env=env, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def changed_files():
    files = set()
    for args in (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        try:
            out = sh(args, ROOT, timeout=20)
            if out.returncode == 0:
                files.update(line for line in out.stdout.splitlines() if line)
        except Exception:
            pass
    return files


def run_gate(label, args, cwd, env=None):
    """Return None on pass/fail-open, or a failure report string."""
    try:
        proc = sh(args, cwd, env=env)
    except subprocess.TimeoutExpired:
        return f"### {label}: TIMED OUT after 240s\n`{' '.join(args)}`"
    except FileNotFoundError:
        return None  # interpreter/tool missing -> environment, fail open
    if proc.returncode == 0:
        return None
    tail = proc.stdout[-TAIL:] if proc.stdout else "(no output)"
    return f"### {label}: FAILED (exit {proc.returncode})\n```\n{tail}\n```"


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if payload.get("status") != "completed":
        print("{}")
        return

    files = changed_files()
    backend_touched = any(f.startswith(BACKEND_PREFIXES) for f in files)
    frontend_touched = any(f.startswith(FRONTEND_PREFIXES) for f in files)
    if not (backend_touched or frontend_touched):
        print("{}")
        return

    failures = []

    if backend_touched:
        backend = os.path.join(ROOT, "backend")
        env = {k: v for k, v in os.environ.items() if k != "API_BASE"}
        if os.path.isdir(os.path.join(backend, ".venv")):
            failures.append(run_gate(
                "backend offline unit tests",
                # -o addopts= drops the ini's -v/--durations so the output
                # tail is the failure summary, not the timing table.
                ["uv", "run", "pytest", *OFFLINE_PYTEST_ARGS, "-q", "-o",
                 "addopts=", "--tb=short", "-p", "no:cacheprovider"],
                backend, env,
            ))
            failures.append(run_gate(
                "behavioral evals",
                ["uv", "run", "python", "-m", "evals.run"],
                backend, env,
            ))

    if frontend_touched:
        frontend = os.path.join(ROOT, "frontend")
        if os.path.isdir(os.path.join(frontend, "node_modules")):
            failures.append(run_gate(
                "frontend unit tests", ["npm", "run", "-s", "test"], frontend,
            ))
            failures.append(run_gate(
                "frontend type-check", ["npm", "run", "-s", "type-check"], frontend,
            ))

    failures = [f for f in failures if f]
    if not failures:
        print("{}")
        return

    message = (
        "Stop-hook verification gate failed — the turn may not end while "
        "these fast offline checks are red. Fix the failures (or the test "
        "expectations, if the behavior change is intentional), then finish.\n\n"
        + "\n\n".join(failures)
        + "\n\nRe-run locally: backend `cd backend && env -u API_BASE uv run "
        "pytest <offline tests> -q && uv run python -m evals.run`; frontend "
        "`cd frontend && npm run test && npm run type-check`. "
        "If a failure is purely environmental (missing services/deps you "
        "cannot install), state that explicitly in your final answer."
    )
    print(json.dumps({"followup_message": message}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("{}")  # never trap the agent on hook bugs
