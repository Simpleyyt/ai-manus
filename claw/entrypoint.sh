#!/bin/bash
set -e

# If arguments are provided, run them instead of the gateway. This makes the
# compose "prevent claw from starting" override (entrypoint/command:
# /bin/sh -c "exit 0") work even with compose implementations that pass the
# override as container args to the image entrypoint instead of replacing it.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

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

# Start OpenClaw gateway as a child process so this script stays PID 1 and can
# act as a watchdog: forward shutdown signals and force-kill if the gateway
# does not exit within the grace period. This guarantees the container always
# exits when the TTL expires (or on docker stop), even if the Node process
# hangs during graceful shutdown.
CLAW_TTL_SECONDS="${CLAW_TTL_SECONDS:-0}"
CLAW_SHUTDOWN_GRACE_SECONDS="${CLAW_SHUTDOWN_GRACE_SECONDS:-30}"

openclaw gateway &
GATEWAY_PID=$!

shutdown_gateway() {
    echo "[entrypoint] Shutting down OpenClaw gateway (pid ${GATEWAY_PID})"
    kill -TERM "${GATEWAY_PID}" 2>/dev/null || true
    for _ in $(seq 1 "${CLAW_SHUTDOWN_GRACE_SECONDS}"); do
        if ! kill -0 "${GATEWAY_PID}" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done
    echo "[entrypoint] Gateway did not stop within ${CLAW_SHUTDOWN_GRACE_SECONDS}s, force killing"
    kill -KILL "${GATEWAY_PID}" 2>/dev/null || true
}
trap shutdown_gateway TERM INT

if [ "${CLAW_TTL_SECONDS}" -gt 0 ] 2>/dev/null; then
    echo "[entrypoint] TTL set to ${CLAW_TTL_SECONDS} seconds, will shutdown automatically"
    (
        sleep "${CLAW_TTL_SECONDS}"
        echo "[entrypoint] TTL expired after ${CLAW_TTL_SECONDS} seconds, shutting down"
        kill -TERM $$ 2>/dev/null || true
    ) &
fi

# Wait for the gateway to exit. The first wait may be interrupted by the TERM
# trap; wait again to collect the real exit status after the trap returns.
set +e
wait "${GATEWAY_PID}"
wait "${GATEWAY_PID}" 2>/dev/null
EXIT_CODE=$?
echo "[entrypoint] OpenClaw gateway exited with code ${EXIT_CODE}"
exit "${EXIT_CODE}"
