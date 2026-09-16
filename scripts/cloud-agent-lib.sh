#!/usr/bin/env bash
# Shared helpers for Cloud Agent install/start. Sourced, not executed.

cloud_agent_repo_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  echo "$here"
}

cloud_agent_wait_for_backend() {
  local i=0
  while [ "$i" -lt 90 ]; do
    if curl -sf "http://127.0.0.1:8000/docs" >/dev/null 2>&1; then
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  return 1
}

cloud_agent_ensure_path() {
  export PATH="${HOME}/.local/bin:${PATH}"
  if [ -f "${HOME}/.local/bin/env" ]; then
    # shellcheck disable=SC1091
    source "${HOME}/.local/bin/env"
  fi
  if [ -f "${HOME}/.bashrc" ] && ! grep -q 'HOME/.local/bin' "${HOME}/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
  fi
}

cloud_agent_ensure_env_file() {
  local root="$1"
  if [ ! -f "${root}/.env" ]; then
    cp "${root}/.env.example" "${root}/.env"
  fi
  python3 - "$root" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1]) / ".env"
text = path.read_text()

def upsert(text: str, key: str, value: str, only_if_empty: bool = False) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    match = pattern.search(text)
    if match:
        current = match.group(0).split("=", 1)[1]
        if only_if_empty and current != "":
            return text
        return pattern.sub(f"{key}={value}", text, count=1)
    if not text.endswith("\n"):
        text += "\n"
    return text + f"{key}={value}\n"

text = upsert(text, "API_KEY", "test", only_if_empty=True)
text = upsert(text, "AUTH_PROVIDER", "none")
path.write_text(text)
PY
}

cloud_agent_ensure_docker_packages() {
  if command -v docker >/dev/null 2>&1 && command -v dockerd >/dev/null 2>&1 && command -v fuse-overlayfs >/dev/null 2>&1; then
    return 0
  fi
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get \
    -o Dpkg::Options::="--force-confold" \
    install -y --no-install-recommends \
    docker.io docker-compose-v2 fuse-overlayfs iptables
}

cloud_agent_ensure_iptables_legacy() {
  if [ -x /usr/sbin/iptables-legacy ]; then
    sudo update-alternatives --set iptables /usr/sbin/iptables-legacy >/dev/null
  fi
  if [ -x /usr/sbin/ip6tables-legacy ]; then
    sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy >/dev/null || true
  fi
}

cloud_agent_write_daemon_json() {
  sudo mkdir -p /etc/docker
  sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "iptables": true,
  "ip6tables": false
}
EOF
}

cloud_agent_wait_for_docker() {
  local i
  for i in $(seq 1 30); do
    if sudo docker info >/dev/null 2>&1; then
      sudo chmod 666 /var/run/docker.sock || true
      return 0
    fi
    sleep 1
  done
  return 1
}

cloud_agent_restart_dockerd() {
  local pid
  pid="$(pidof dockerd || true)"
  if [ -n "$pid" ]; then
    sudo kill $pid
    local i
    for i in $(seq 1 30); do
      pidof dockerd >/dev/null 2>&1 || break
      sleep 0.2
    done
  fi
  sudo dockerd >/tmp/dockerd.log 2>&1 &
  if ! cloud_agent_wait_for_docker; then
    echo "dockerd failed to become ready" >&2
    tail -50 /tmp/dockerd.log >&2 || true
    return 1
  fi
}

cloud_agent_ensure_dockerd() {
  cloud_agent_ensure_docker_packages
  cloud_agent_ensure_iptables_legacy
  cloud_agent_write_daemon_json
  sudo usermod -aG docker "$(id -un)" 2>/dev/null || true

  if ! command -v dockerd >/dev/null 2>&1; then
    echo "dockerd is not installed" >&2
    return 1
  fi

  if [ -S /var/run/docker.sock ] && sudo docker info >/dev/null 2>&1; then
    sudo chmod 666 /var/run/docker.sock || true
    return 0
  fi

  cloud_agent_restart_dockerd
}
