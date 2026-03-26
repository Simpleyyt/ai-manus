#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "  ___  ___   __  __                       "
    echo " / _ \|_ _| |  \/  | __ _ _ __  _   _ ___ "
    echo "| |_| || |  | |\/| |/ _\` | '_ \| | | / __|"
    echo "|  _  || |  | |  | | (_| | | | | |_| \__ \\"
    echo "|_| |_|___| |_|  |_|\__,_|_| |_|\__,_|___/"
    echo -e "${NC}"
    echo -e "${GREEN}AI Manus Local Deployment Setup${NC}"
    echo ""
}

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

generate_random_string() {
    local length=${1:-32}
    if check_command openssl; then
        openssl rand -hex "$((length / 2))"
    elif [ -f /dev/urandom ]; then
        head -c "$((length / 2))" /dev/urandom | od -An -tx1 | tr -d ' \n' | head -c "$length"
    else
        date +%s%N | sha256sum | head -c "$length"
    fi
}

# ==============================
# Step 1: Check Prerequisites
# ==============================
check_prerequisites() {
    info "Checking prerequisites..."

    # Check Docker
    if ! check_command docker; then
        error "Docker is not installed."
        echo ""
        echo "Please install Docker first:"
        echo "  - Linux:   https://docs.docker.com/engine/install/"
        echo "  - macOS:   https://docs.docker.com/desktop/install/mac-install/"
        echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    fi

    # Check Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi

    local docker_version
    docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    info "Docker version: $docker_version"

    # Check Docker Compose
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE="docker compose"
        local compose_version
        compose_version=$(docker compose version --short 2>/dev/null || echo "unknown")
        info "Docker Compose version: $compose_version (plugin)"
    elif check_command docker-compose; then
        COMPOSE="docker-compose"
        local compose_version
        compose_version=$(docker-compose version --short 2>/dev/null || echo "unknown")
        info "Docker Compose version: $compose_version (standalone)"
    else
        error "Docker Compose is not installed."
        echo ""
        echo "Please install Docker Compose:"
        echo "  https://docs.docker.com/compose/install/"
        exit 1
    fi

    info "All prerequisites satisfied."
    echo ""
}

# ==============================
# Step 2: Configure Environment
# ==============================
configure_env() {
    info "Configuring environment..."

    if [ -f .env ]; then
        warn ".env file already exists."
        read -rp "Overwrite existing .env file? [y/N] " overwrite
        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            info "Keeping existing .env file."
            return
        fi
    fi

    if [ ! -f .env.example ]; then
        error ".env.example not found. Please run this script from the project root directory."
        exit 1
    fi

    cp .env.example .env

    echo ""
    echo -e "${BLUE}=== LLM Model Configuration ===${NC}"
    echo ""
    echo "AI Manus requires an LLM service that supports Function Call."
    echo "Recommended: DeepSeek, OpenAI GPT-4o, or other compatible models."
    echo ""

    # API_BASE
    local default_api_base="https://api.deepseek.com/v1"
    read -rp "API Base URL [$default_api_base]: " api_base
    api_base=${api_base:-$default_api_base}

    # API_KEY
    read -rp "API Key (required): " api_key
    while [ -z "$api_key" ]; do
        warn "API Key is required."
        read -rp "API Key: " api_key
    done

    # MODEL_NAME
    local default_model="deepseek-chat"
    if [[ "$api_base" == *"openai.com"* ]]; then
        default_model="gpt-4o"
    fi
    read -rp "Model Name [$default_model]: " model_name
    model_name=${model_name:-$default_model}

    # MODEL_PROVIDER
    local default_provider="openai"
    read -rp "Model Provider [$default_provider]: " model_provider
    model_provider=${model_provider:-$default_provider}

    echo ""
    echo -e "${BLUE}=== Authentication Configuration ===${NC}"
    echo ""
    echo "Authentication modes:"
    echo "  1) local  - Single user, no registration needed (recommended for local use)"
    echo "  2) none   - No authentication"
    echo "  3) password - Email registration with password"
    echo ""
    read -rp "Select authentication mode [1]: " auth_choice
    auth_choice=${auth_choice:-1}

    local auth_provider="local"
    local local_email="admin@example.com"
    local local_password="admin"

    case $auth_choice in
        1)
            auth_provider="local"
            read -rp "Admin email [admin@example.com]: " local_email
            local_email=${local_email:-admin@example.com}
            read -rp "Admin password [admin]: " local_password
            local_password=${local_password:-admin}
            ;;
        2)
            auth_provider="none"
            ;;
        3)
            auth_provider="password"
            ;;
        *)
            auth_provider="local"
            ;;
    esac

    echo ""
    echo -e "${BLUE}=== Search Configuration ===${NC}"
    echo ""
    echo "Search providers (no API key needed for *_web options):"
    echo "  1) bing_web  - Bing web scraping (default, no key needed)"
    echo "  2) baidu_web - Baidu web scraping (no key needed)"
    echo "  3) bing      - Bing API (requires API key)"
    echo "  4) google    - Google API (requires API key)"
    echo "  5) tavily    - Tavily API (requires API key)"
    echo ""
    read -rp "Select search provider [1]: " search_choice
    search_choice=${search_choice:-1}

    local search_provider="bing_web"
    case $search_choice in
        1) search_provider="bing_web" ;;
        2) search_provider="baidu_web" ;;
        3) search_provider="bing" ;;
        4) search_provider="google" ;;
        5) search_provider="tavily" ;;
        *) search_provider="bing_web" ;;
    esac

    # Generate secure random values
    local jwt_secret
    jwt_secret=$(generate_random_string 64)
    local password_salt
    password_salt=$(generate_random_string 32)

    # Write .env file
    cat > .env << EOF
# ============================================
# AI Manus Configuration
# Generated by setup.sh on $(date '+%Y-%m-%d %H:%M:%S')
# ============================================

# Model provider configuration
API_KEY=${api_key}
API_BASE=${api_base}

# Model configuration
MODEL_NAME=${model_name}
MODEL_PROVIDER=${model_provider}
TEMPERATURE=0.7
MAX_TOKENS=2000

# MongoDB configuration
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DATABASE=manus

# Redis configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Sandbox configuration
SANDBOX_IMAGE=simpleyyt/manus-sandbox
SANDBOX_NAME_PREFIX=sandbox
SANDBOX_TTL_MINUTES=30
SANDBOX_NETWORK=manus-network

# Search engine configuration
SEARCH_PROVIDER=${search_provider}

# Auth configuration
AUTH_PROVIDER=${auth_provider}
LOCAL_AUTH_EMAIL=${local_email}
LOCAL_AUTH_PASSWORD=${local_password}

# Password auth configuration
PASSWORD_SALT=${password_salt}
PASSWORD_HASH_ROUNDS=10

# JWT configuration
JWT_SECRET_KEY=${jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Log configuration
LOG_LEVEL=INFO
EOF

    info ".env file created successfully."
    echo ""
}

# ==============================
# Step 3: Build / Pull and Start
# ==============================
build_and_start() {
    local mode="${1:-image}"

    if [ "$mode" = "source" ]; then
        info "Building images from source code..."
        $COMPOSE -f docker-compose.yml build
        echo ""
    fi

    info "Starting services..."
    $COMPOSE -f docker-compose.yml up -d

    echo ""
    info "Waiting for services to start..."
    sleep 5

    # Check service status
    local all_healthy=true
    local services=("frontend" "backend" "mongodb" "redis")
    for svc in "${services[@]}"; do
        local status
        status=$($COMPOSE -f docker-compose.yml ps --format '{{.State}}' "$svc" 2>/dev/null || echo "unknown")
        if [[ "$status" == *"running"* ]]; then
            info "  $svc: ${GREEN}running${NC}"
        else
            warn "  $svc: $status"
            all_healthy=false
        fi
    done

    echo ""
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}======================================${NC}"
        echo -e "${GREEN}  AI Manus is running!${NC}"
        echo -e "${GREEN}======================================${NC}"
    else
        warn "Some services may not be fully ready yet. Check logs with:"
        echo "  $COMPOSE -f docker-compose.yml logs -f"
    fi

    echo ""
    echo -e "  Web UI:     ${BLUE}http://localhost:5173${NC}"
    echo -e "  Backend API: ${BLUE}http://localhost:8000${NC}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     $COMPOSE -f docker-compose.yml logs -f"
    echo "  Stop services: $COMPOSE -f docker-compose.yml down"
    echo "  Restart:       $COMPOSE -f docker-compose.yml restart"
    echo "  Reset data:    $COMPOSE -f docker-compose.yml down -v"
    echo ""
}

# ==============================
# Main
# ==============================
main() {
    print_banner

    # Parse arguments
    local skip_config=false
    local build_mode="image"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-config)
                skip_config=true
                shift
                ;;
            --build-from-source)
                build_mode="source"
                shift
                ;;
            -h|--help)
                echo "Usage: ./setup.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-config        Skip interactive configuration (use existing .env)"
                echo "  --build-from-source  Build Docker images from source code"
                echo "  -h, --help           Show this help message"
                echo ""
                echo "Examples:"
                echo "  ./setup.sh                        # Interactive setup with pre-built images"
                echo "  ./setup.sh --build-from-source    # Build from source and deploy"
                echo "  ./setup.sh --skip-config          # Skip config, use existing .env"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Run './setup.sh --help' for usage information."
                exit 1
                ;;
        esac
    done

    check_prerequisites

    if [ "$skip_config" = false ]; then
        configure_env
    else
        if [ ! -f .env ]; then
            error ".env file not found. Run without --skip-config to create one."
            exit 1
        fi
        info "Using existing .env configuration."
    fi

    echo -e "${BLUE}=== Deployment ===${NC}"
    echo ""

    if [ "$build_mode" = "source" ]; then
        info "Will build Docker images from local source code."
    else
        info "Will use pre-built Docker images from Docker Hub."
    fi
    echo ""

    build_and_start "$build_mode"
}

main "$@"
