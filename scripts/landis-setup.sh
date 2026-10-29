#!/usr/bin/env bash
# Landis AI — setup script for free replica (Docker + SearXNG + Ollama)
set -e

echo "== Landis AI Setup (grátis) =="
echo "Step 1: check Docker"
docker --version || { echo "Docker missing"; exit 1; }
docker compose version || { echo "docker compose missing"; exit 1; }

echo "Step 2: SearXNG (free search, unlimited)"
if ! docker ps | grep -q searxng; then
  echo "Starting SearXNG on :8081..."
  docker run -d --name searxng --restart unless-stopped -p 8081:8080 searxng/searxng:latest || true
  echo "Edit searxng/settings.yml → search.formats: [\"html\", \"json\"] then restart"
else
  echo "SearXNG already running"
fi

echo "Step 3: Ollama (local LLM)"
if command -v ollama >/dev/null 2>&1; then
  echo "Ollama found: $(ollama --version)"
  echo "Pull model (choose one):"
  echo "  ollama pull gpt-oss:20b       # 16GB RAM"
  echo "  ollama pull qwen3-coder:30b   # 24-32GB RAM (best)"
  echo "  ollama pull qwen3:8b          # 8-12GB RAM"
else
  echo "Ollama not found — install from https://ollama.com or use OpenRouter free"
fi

echo "Step 4: .env"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it!"
  echo "For 100% free local:"
  echo "  MODEL_PROVIDER=ollama"
  echo "  MODEL_NAME=qwen3-coder:30b"
  echo "  API_BASE=http://host.docker.internal:11434/v1"
  echo "  API_KEY=ollama"
  echo "  SEARCH_PROVIDER=searxng"
  echo "  SEARXNG_URL=http://searxng:8080"
else
  echo ".env exists"
fi

echo "Step 5: start stack"
echo "Run: ./dev.sh up -d"
echo "Open http://localhost:5173"
echo "Docs: LANDIS_AI_REPLICA.md and docs/en/landis-replica.md"
