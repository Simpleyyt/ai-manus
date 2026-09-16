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

(cd "${ROOT}/backend" && uv sync --frozen)
(cd "${ROOT}/sandbox" && uv sync --frozen)
(cd "${ROOT}/frontend" && npm ci)
python3 -m pip install --user -r "${ROOT}/mockserver/requirements.txt"
(cd "${ROOT}/frontend" && npx playwright install chromium)

if cloud_agent_ensure_dockerd; then
  ./dev.sh build
else
  echo "Docker is unavailable; native backend/frontend/sandbox deps are installed."
  echo "Full-stack compose commands (./dev.sh) will not work until dockerd starts."
fi
