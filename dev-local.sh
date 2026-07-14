#!/bin/bash
#
# dev-local.sh — Run the AI Manus development stack WITHOUT Docker.
#
# Starts (as plain host processes):
#   - mockserver  (port 8090)  mock LLM server
#   - sandbox     (port 8080)  sandbox API in standalone mode (no Chrome/VNC)
#   - backend     (port 8000)  FastAPI backend
#   - frontend    (port 5173)  Vite dev server
#   - mongodb     (port 27017) only if `mongod` is installed and nothing is listening
#   - redis       (port 6379)  only if `redis-server` is installed and nothing is listening
#
# MongoDB and Redis are required by the backend. If they are already running
# (natively or otherwise) on localhost, they are reused as-is.
#
# Usage:
#   ./dev-local.sh up [service...]      # start all (or selected) services
#   ./dev-local.sh down [service...]    # stop all (or selected) services
#   ./dev-local.sh status               # show service status
#   ./dev-local.sh logs <service>       # tail logs of a service
#
# Configuration is read from .env (if present). Docker-compose hostnames
# (mongodb / redis / mockserver / backend) are automatically rewritten to
# localhost, so the same .env works for both ./dev.sh and ./dev-local.sh.
#
# NOTE: the sandbox runs directly on YOUR machine — shell/file tools executed
# by the agent operate on the host. Browser tools are unavailable in this
# mode (no Chrome/CDP); the corresponding tool calls will return errors.

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.dev-local"
LOG_DIR="$RUN_DIR/logs"
DATA_DIR="$RUN_DIR/data"
mkdir -p "$RUN_DIR" "$LOG_DIR" "$DATA_DIR"

ALL_SERVICES=(mongodb redis mockserver sandbox backend frontend)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { echo "[dev-local] $*"; }
warn() { echo "[dev-local] WARN: $*" >&2; }
die()  { echo "[dev-local] ERROR: $*" >&2; exit 1; }

port_in_use() {
    # $1 = port
    if command -v python3 &>/dev/null; then
        python3 - "$1" <<'EOF'
import socket, sys
s = socket.socket()
s.settimeout(0.5)
sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
EOF
    else
        (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && { exec 3>&-; return 0; } || return 1
    fi
}

pid_file() { echo "$RUN_DIR/$1.pid"; }

service_pid() {
    local f
    f="$(pid_file "$1")"
    [ -f "$f" ] && cat "$f" 2>/dev/null || true
}

service_running() {
    local pid
    pid="$(service_pid "$1")"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

start_process() {
    # $1 = service name, $2 = working dir, rest = command
    local name="$1" dir="$2"
    shift 2
    if service_running "$name"; then
        log "$name already running (pid $(service_pid "$name"))"
        return 0
    fi
    log "starting $name ..."
    # setsid (when available) makes the service a process-group leader so
    # `down` can kill the whole tree (uv/npm spawn children).
    local runner=()
    command -v setsid &>/dev/null && runner=(setsid)
    (cd "$dir" && nohup "${runner[@]}" "$@" >>"$LOG_DIR/$name.log" 2>&1 &
     echo $! >"$(pid_file "$name")")
    sleep 1
    if service_running "$name"; then
        log "$name started (pid $(service_pid "$name"), log: .dev-local/logs/$name.log)"
    else
        warn "$name failed to start — check .dev-local/logs/$name.log"
        return 1
    fi
}

stop_process() {
    local name="$1" pid
    pid="$(service_pid "$name")"
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        log "$name is not running"
        rm -f "$(pid_file "$name")"
        return 0
    fi
    log "stopping $name (pid $pid) ..."
    # Kill the whole process group when possible (uv/npm spawn children)
    kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null
    for _ in $(seq 1 20); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 -- -"$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
    fi
    rm -f "$(pid_file "$name")"
    log "$name stopped"
}

require_cmd() {
    command -v "$1" &>/dev/null || die "'$1' is required but not installed. $2"
}

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_env() {
    # Load .env then rewrite docker-compose hostnames for host networking.
    if [ -f "$ROOT_DIR/.env" ]; then
        set -a
        # shellcheck disable=SC1091
        source "$ROOT_DIR/.env"
        set +a
    fi

    # Rewrite compose service hostnames to localhost
    export MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27017}"
    MONGODB_URI="${MONGODB_URI/mongodb:\/\/mongodb/mongodb://localhost}"
    export REDIS_HOST="${REDIS_HOST:-localhost}"
    [ "$REDIS_HOST" = "redis" ] && export REDIS_HOST=localhost
    export API_BASE="${API_BASE:-http://localhost:8090/v1}"
    API_BASE="${API_BASE/\/\/mockserver/\/\/localhost}"
    export API_KEY="${API_KEY:-local-dev-key}"

    # Point the backend at the host sandbox / claw
    export SANDBOX_ADDRESS="${SANDBOX_ADDRESS:-127.0.0.1}"
    [ "$SANDBOX_ADDRESS" = "sandbox" ] && export SANDBOX_ADDRESS=127.0.0.1
    export MANUS_API_BASE_URL="${MANUS_API_BASE_URL:-http://localhost:8000}"
    MANUS_API_BASE_URL="${MANUS_API_BASE_URL/\/\/backend/\/\/localhost}"

    # Development ergonomics
    export AUTH_PROVIDER="${AUTH_PROVIDER:-none}"
    export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
    export MCP_CONFIG_PATH="${MCP_CONFIG_PATH:-$ROOT_DIR/mcp.json}"
}

# ---------------------------------------------------------------------------
# Service definitions
# ---------------------------------------------------------------------------

start_mongodb() {
    if port_in_use 27017; then
        log "mongodb: something is already listening on 27017 — reusing it"
        return 0
    fi
    if ! command -v mongod &>/dev/null; then
        die "MongoDB is not reachable on localhost:27017 and 'mongod' is not installed.
  Install MongoDB (https://www.mongodb.com/docs/manual/installation/) or start
  one yourself, then re-run. Example (Debian/Ubuntu): sudo apt install mongodb-org"
    fi
    mkdir -p "$DATA_DIR/mongodb"
    start_process mongodb "$ROOT_DIR" \
        mongod --dbpath "$DATA_DIR/mongodb" --bind_ip 127.0.0.1 --port 27017
}

start_redis() {
    if port_in_use 6379; then
        log "redis: something is already listening on 6379 — reusing it"
        return 0
    fi
    if ! command -v redis-server &>/dev/null; then
        die "Redis is not reachable on localhost:6379 and 'redis-server' is not installed.
  Install Redis (e.g. sudo apt install redis-server / brew install redis) or
  start one yourself, then re-run."
    fi
    mkdir -p "$DATA_DIR/redis"
    start_process redis "$ROOT_DIR" \
        redis-server --port 6379 --bind 127.0.0.1 --dir "$DATA_DIR/redis" --save ''
}

start_mockserver() {
    require_cmd uv "Install it from https://docs.astral.sh/uv/"
    if [ ! -d "$ROOT_DIR/mockserver/.venv" ]; then
        log "mockserver: creating virtualenv ..."
        (cd "$ROOT_DIR/mockserver" && uv venv .venv -q \
            && uv pip install -q --python .venv/bin/python -r requirements.txt) \
            || die "failed to install mockserver dependencies"
    fi
    start_process mockserver "$ROOT_DIR/mockserver" \
        .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8090
}

start_sandbox() {
    require_cmd uv "Install it from https://docs.astral.sh/uv/"
    log "sandbox: syncing dependencies ..."
    (cd "$ROOT_DIR/sandbox" && uv sync -q) || die "failed to sync sandbox dependencies"
    # Standalone mode: no supervisord / Chrome / VNC. Shell & file tools work,
    # browser tools are unavailable.
    start_process sandbox "$ROOT_DIR/sandbox" \
        env LOG_LEVEL="$LOG_LEVEL" \
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
}

start_backend() {
    require_cmd uv "Install it from https://docs.astral.sh/uv/"
    log "backend: syncing dependencies ..."
    (cd "$ROOT_DIR/backend" && uv sync -q) || die "failed to sync backend dependencies"
    start_process backend "$ROOT_DIR/backend" \
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
        --timeout-graceful-shutdown 0
}

start_frontend() {
    require_cmd npm "Install Node.js (https://nodejs.org/)"
    if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
        log "frontend: installing dependencies ..."
        (cd "$ROOT_DIR/frontend" && npm install --no-audit --no-fund) \
            || die "failed to install frontend dependencies"
    fi
    start_process frontend "$ROOT_DIR/frontend" \
        env BACKEND_URL=http://localhost:8000 npm run dev -- --host 0.0.0.0
}

start_service() {
    case "$1" in
        mongodb)    start_mongodb ;;
        redis)      start_redis ;;
        mockserver) start_mockserver ;;
        sandbox)    start_sandbox ;;
        backend)    start_backend ;;
        frontend)   start_frontend ;;
        *) die "unknown service: $1 (available: ${ALL_SERVICES[*]})" ;;
    esac
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

cmd_up() {
    load_env
    local services=("$@")
    [ ${#services[@]} -eq 0 ] && services=("${ALL_SERVICES[@]}")
    for s in "${services[@]}"; do
        start_service "$s"
    done
    echo
    log "stack is up:"
    log "  frontend:   http://localhost:5173"
    log "  backend:    http://localhost:8000  (docs: /docs)"
    log "  sandbox:    http://localhost:8080  (standalone mode, no browser)"
    log "  mockserver: http://localhost:8090"
    log "logs: .dev-local/logs/  |  stop: ./dev-local.sh down"
}

cmd_down() {
    local services=("$@")
    [ ${#services[@]} -eq 0 ] && services=(frontend backend sandbox mockserver redis mongodb)
    for s in "${services[@]}"; do
        stop_process "$s"
    done
}

cmd_status() {
    for s in "${ALL_SERVICES[@]}"; do
        if service_running "$s"; then
            echo "  $s: running (pid $(service_pid "$s"))"
        else
            echo "  $s: stopped"
        fi
    done
}

cmd_logs() {
    [ $# -ge 1 ] || die "usage: ./dev-local.sh logs <service>"
    local f="$LOG_DIR/$1.log"
    [ -f "$f" ] || die "no log file for '$1' ($f)"
    tail -n 100 -f "$f"
}

usage() {
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
}

case "${1:-}" in
    up)     shift; cmd_up "$@" ;;
    down)   shift; cmd_down "$@" ;;
    status) cmd_status ;;
    logs)   shift; cmd_logs "$@" ;;
    -h|--help|help|"") usage ;;
    *) die "unknown command: $1 (use up / down / status / logs)" ;;
esac
