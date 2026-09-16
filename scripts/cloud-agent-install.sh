#!/usr/bin/env bash
# Idempotent Cloud Agent install: native toolchains plus Docker images.
# Docker is not present in the current Cloud Agent base image; install it
# here and pre-build compose images. Do not leave the stack running.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/cloud-agent-lib.sh"

ROOT="$(cloud_agent_repo_root)"
cd "$ROOT"

cloud_agent_ensure_path
cloud_agent_ensure_env_file "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  cloud_agent_ensure_path
fi

(cd "${ROOT}/frontend" && npm ci)
python3 -m pip install --user -r "${ROOT}/mockserver/requirements.txt"
(cd "${ROOT}/frontend" && npx playwright install chromium)

if cloud_agent_ensure_dockerd; then
  ./dev.sh pull
  ./dev.sh build
  # Compose copies host backend/.venv into a new anonymous volume on first
  # create. Bring the stack up once with no host venv so the container can
  # populate a compatible environment, then stop (processes do not persist).
  rm -rf "${ROOT}/backend/.venv" "${ROOT}/sandbox/.venv"
  ./dev.sh up -d
  if cloud_agent_wait_for_backend; then
    # Docker creates root-owned mountpoints for the anonymous /app/.venv volumes.
    sudo chown -R "$(id -un):$(id -gn)" "${ROOT}/backend/.venv" "${ROOT}/sandbox/.venv" 2>/dev/null || true
    ./dev.sh stop
  else
    echo "Backend did not become ready during install" >&2
    ./dev.sh ps >&2 || true
    ./dev.sh logs --tail=80 backend >&2 || true
    exit 1
  fi
else
  echo "Docker is unavailable; native backend/frontend/sandbox deps will still be installed."
  echo "Full-stack compose commands (./dev.sh) will not work until dockerd starts."
fi

# Host venvs for offline tests. Safe after compose volumes already exist.
uv sync --frozen --directory "${ROOT}/backend"
uv sync --frozen --directory "${ROOT}/sandbox"
