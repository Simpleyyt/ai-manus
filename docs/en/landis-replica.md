# Landis AI — Replica Guide

> How to run a Manus-like agent for free, based on the "Como montar um Manus gratuito" guide (Oct 2026) and the Landis AI scaffold in this branch.

## Quick Start (100% Free)

### 1. SearXNG (unlimited search, no key)

```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng
# edit searxng settings.yml → search.formats: ["html", "json"]
```

Set in `.env`:

```ini
SEARCH_PROVIDER=searxng
SEARXNG_URL=http://searxng:8080
```

### 2. Ollama (local LLM, no quota)

```bash
# install Ollama: https://ollama.com
ollama pull qwen3-coder:30b   # 24-32GB RAM, best for agents
# or gpt-oss:20b for 16GB, qwen3:8b for 8GB
```

Set in `.env`:

```ini
MODEL_PROVIDER=ollama
MODEL_NAME=qwen3-coder:30b
API_BASE=http://host.docker.internal:11434/v1
API_KEY=ollama
```

### 3. Run Landis

```bash
cp .env.example .env
./dev.sh up -d
# http://localhost:5173
```

### 4. Wide Research (parallel)

```bash
curl -X POST http://localhost:8000/api/v1/wide-research \
  -H "Content-Type: application/json" \
  -d '{"goal":"Compare 100 notebooks","items":["MacBook Air","ThinkPad X1","XPS 13"],"max_parallel":3}'
```

### 5. Automations

```bash
# Create a daily report automation
curl -X POST http://localhost:8000/api/v1/automations \
  -H "Content-Type: application/json" \
  -d '{"name":"Daily report","task_prompt":"Check GitHub PRs and email summary","trigger_type":"schedule","schedule":{"cron":"0 9 * * *"}}'

# List
curl http://localhost:8000/api/v1/automations
```

### 6. Cloud Computer

```bash
curl -X POST "http://localhost:8000/api/v1/cloud-computers?name=MyCloud&provider=docker"
```

## LLM Providers (Free Tiers Oct 2026)

| Provider | Free limit | When to use |
|----------|-----------|-------------|
| Ollama | ∞ (local) | Main |
| OpenRouter :free | 20 req/min, 50/dia | Reserve |
| Groq | 30/min, 1k/day, 200k tokens/day | Short tasks |
| Gemini (AI Studio) | varies | Reserve |
| Cloudflare Workers AI | 10k neurons/day | Fixed quota |

> All free tiers are via `MODEL_PROVIDER` + `API_BASE` + `API_KEY`. See `docs/en/configuration.md`.

## Search Providers

| Provider | Key | Notes |
|----------|-----|-------|
| `searxng` | no | Self-hosted, unlimited ✅ |
| `bing_web` | no | Scraping, default |
| `tavily` | `TAVILY_API_KEY` | 1k credits/mo free |
| `exa` | `EXA_API_KEY` | AI-first |
| `firecrawl` | `FIRECRAWL_API_KEY` | Scraping + markdown |
| `brave` | `BRAVE_SEARCH_API_KEY` | $5/mo after Feb 2026 |
| `serper` | `SERPER_API_KEY` | Google via Serper |
| `custom` | `SEARCH_API_URL` + `SEARCH_API_KEY` | Any REST API |

## Security Checklist

- [ ] `AUTH_PROVIDER=password` with strong `JWT_SECRET_KEY` and `PASSWORD_SALT`
- [ ] Never put secrets inside sandbox container
- [ ] Grant minimal OAuth scopes, separate test/prod accounts
- [ ] Require human approval before send/publish/buy/delete
- [ ] Review sources, formulas, code, recipients
- [ ] Keep backups, set credit/time limits, monitor connector logs
- [ ] Treat web/email content as untrusted (prompt injection)

## Manus → Landis mapping

See `LANDIS_AI_REPLICA.md` for full mapping.
