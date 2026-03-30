#!/bin/bash
set -e

CONFIG_DIR="/home/node/.openclaw"
CONFIG_FILE="${CONFIG_DIR}/openclaw.json"
mkdir -p "${CONFIG_DIR}/workspace"

# Generate a secure gateway token if not provided
if [ -z "${OPENCLAW_GATEWAY_TOKEN}" ]; then
    OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 24 2>/dev/null || node -e "console.log(require('crypto').randomBytes(24).toString('hex'))")
    export OPENCLAW_GATEWAY_TOKEN
fi

echo "[entrypoint] Gateway token: ${OPENCLAW_GATEWAY_TOKEN}"
echo "[entrypoint] Manus API base URL: ${MANUS_API_BASE_URL:-http://backend:8000}/v1"

# Write openclaw.json configuration
cat > "${CONFIG_FILE}" << EOF
{
  "meta": {
    "lastTouchedVersion": "2026.2.13"
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "manus-proxy/default"
      },
      "workspace": "/home/node/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 4
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "auth": {
      "mode": "token",
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    }
  },
  "plugins": {
    "load": {
      "paths": [
        "/home/node/.openclaw/extensions/manus-claw"
      ]
    },
    "entries": {
      "manus-claw": {
        "enabled": true,
        "config": {
          "gateway": {
            "url": "ws://127.0.0.1:18789",
            "token": "${OPENCLAW_GATEWAY_TOKEN}",
            "agentId": "main"
          },
          "server": {
            "port": 18788,
            "host": "0.0.0.0"
          },
          "retry": {
            "baseMs": 1000,
            "maxMs": 60000,
            "maxAttempts": 0
          },
          "log": {
            "enabled": true,
            "verbose": false
          }
        }
      }
    }
  },
  "models": {
    "mode": "merge",
    "providers": {
      "manus-proxy": {
        "baseUrl": "${MANUS_API_BASE_URL:-http://backend:8000}/v1",
        "apiKey": "${MANUS_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "default",
            "name": "default",
            "contextWindow": 128000,
            "maxTokens": 8192
          }
        ]
      }
    }
  }
}
EOF

echo "[entrypoint] Configuration written to ${CONFIG_FILE}"

# TTL auto-shutdown (must be set up before starting OpenClaw)
CLAW_TTL_SECONDS="${CLAW_TTL_SECONDS:-0}"
if [ "${CLAW_TTL_SECONDS}" -gt 0 ] 2>/dev/null; then
    echo "[entrypoint] TTL set to ${CLAW_TTL_SECONDS} seconds, will shutdown automatically"
    (
        sleep "${CLAW_TTL_SECONDS}"
        echo "[entrypoint] TTL expired after ${CLAW_TTL_SECONDS} seconds, shutting down"
        kill -TERM $$ 2>/dev/null || true
    ) &
fi

# Start OpenClaw gateway
exec openclaw gateway
