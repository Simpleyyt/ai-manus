#!/usr/bin/env bash
# Per-boot Cloud Agent start: dockerd + docker compose dev stack.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/cloud-agent-lib.sh"

ROOT="$(cloud_agent_repo_root)"
cd "$ROOT"

cloud_agent_ensure_path
cloud_agent_ensure_env_file "$ROOT"

if ! cloud_agent_ensure_dockerd; then
  echo "Skipping compose stack; dockerd is not available."
  exit 0
fi

./dev.sh up -d

ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl -sf "http://127.0.0.1:8000/docs" >/dev/null 2>&1; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 2
done

if [ "$ready" -ne 1 ]; then
  echo "Backend did not become ready on :8000" >&2
  ./dev.sh ps >&2 || true
  ./dev.sh logs --tail=80 backend >&2 || true
  exit 1
fi

echo "Dev stack is up (backend http://127.0.0.1:8000)."
