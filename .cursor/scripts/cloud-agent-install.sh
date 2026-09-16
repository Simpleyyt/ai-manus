#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="${HOME}/.local/bin:${PATH}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  sed -i 's/^AUTH_PROVIDER=.*/AUTH_PROVIDER=none/' .env
  if grep -q '^API_KEY=$' .env; then
    sed -i 's/^API_KEY=$/API_KEY=test/' .env
  fi
fi

echo "Installing backend dependencies..."
(cd backend && uv sync --frozen)

echo "Installing frontend dependencies..."
(cd frontend && npm ci)

echo "Installing sandbox dependencies..."
(cd sandbox && uv sync --frozen)

echo "Installing mockserver dependencies..."
(cd mockserver && python3 -m pip install --user -r requirements.txt -q)

echo "Cloud Agent install complete."
