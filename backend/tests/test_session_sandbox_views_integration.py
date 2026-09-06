"""
Integration tests for session shell/file view API (DTO -> API response chain).

Requires a running dev stack:
  ./dev.sh up -d mongodb redis sandbox mockserver backend

These tests hit http://localhost:8000 and prepare sandbox state via
http://localhost:8080, then attach the Manus session to the dev sandbox
through MongoDB (same sandbox_id the backend assigns in development).
"""

from __future__ import annotations

import time
import uuid

import pytest
import requests
from pymongo import MongoClient

from conftest import BASE_URL

SANDBOX_URL = "http://localhost:8080/api/v1"
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DATABASE = "manus"
DEV_SANDBOX_ID = "dev-sandbox"
BACKEND_READY_TIMEOUT = 180
SANDBOX_READY_TIMEOUT = 120


def _wait_for_url(url: str, timeout: float, label: str) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return
            last_error = f"status {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(2)
    pytest.fail(f"{label} not ready after {timeout}s: {last_error}")


@pytest.fixture(scope="module")
def live_stack():
    """Fail fast when the integration stack is not running."""
    _wait_for_url(f"{BASE_URL}/config/frontend", BACKEND_READY_TIMEOUT, "backend")
    _wait_for_url(f"{SANDBOX_URL.replace('/api/v1', '')}/docs", SANDBOX_READY_TIMEOUT, "sandbox")


@pytest.fixture
def mongo_sessions():
    client = MongoClient(MONGODB_URI)
    collection = client[MONGODB_DATABASE]["sessions"]
    yield collection
    client.close()


@pytest.fixture
def manus_session(client: requests.Session, live_stack, mongo_sessions):
    """Create a Manus session and bind it to the dev sandbox container."""
    response = client.put(f"{BASE_URL}/sessions")
    assert response.status_code == 200, response.text
    session_id = response.json()["data"]["session_id"]

    updated = mongo_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"sandbox_id": DEV_SANDBOX_ID}},
    )
    assert updated.matched_count == 1

    return session_id


def _sandbox_exec(command: str, shell_id: str | None = None) -> str:
    payload = {
        "id": shell_id or "",
        "exec_dir": "/home/ubuntu",
        "command": command,
    }
    response = requests.post(f"{SANDBOX_URL}/shell/exec", json=payload, timeout=30)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]["session_id"]


def _sandbox_write_file(path: str, content: str) -> None:
    response = requests.post(
        f"{SANDBOX_URL}/file/write",
        json={"file": path, "content": content},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("success") is True, body


@pytest.mark.integration
def test_shell_view_api_returns_expected_schema(client, live_stack, manus_session):
    marker = f"integration-shell-{uuid.uuid4().hex[:8]}"
    shell_id = _sandbox_exec(f"echo {marker}")

    # Allow the shell process to finish so output is available.
    time.sleep(1)

    response = client.post(
        f"{BASE_URL}/sessions/{manus_session}/shell",
        json={"session_id": shell_id},
    )
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["code"] == 0
    data = payload["data"]
    assert data["session_id"] == shell_id
    assert marker in data["output"]
    assert isinstance(data.get("console"), list)
    assert data["console"][0]["command"] == f"echo {marker}"


@pytest.mark.integration
def test_file_view_api_returns_expected_schema(client, live_stack, manus_session):
    file_path = f"/tmp/dto-integration-{uuid.uuid4().hex[:8]}.txt"
    expected = "dto integration file body"
    _sandbox_write_file(file_path, expected)

    response = client.post(
        f"{BASE_URL}/sessions/{manus_session}/file",
        json={"file": file_path},
    )
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["code"] == 0
    data = payload["data"]
    assert data["file"] == file_path
    assert expected in data["content"]
