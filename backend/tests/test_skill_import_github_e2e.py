"""Live-stack E2E for POST /api/v1/skills/import/github.

Requires a running backend (./dev.sh up -d mongodb redis backend or local uvicorn)
with AUTH_PROVIDER=none. Hits real GitHub codeload unless SKILL_GITHUB_E2E_URL is unset
and pytest is invoked with -m skill_github_e2e.
"""

import os

import pytest
import requests

from conftest import BASE_URL

DEFAULT_GITHUB_E2E_URL = "https://github.com/win4r/openclaw-workspace"


def _backend_ready() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/skills", timeout=5)
        return response.status_code == 200 and response.json().get("code") == 0
    except requests.RequestException:
        return False


@pytest.mark.skill_github_e2e
def test_import_skill_from_github_live(client):
    if not _backend_ready():
        pytest.skip("Backend not reachable at localhost:8000 with working /skills")

    github_url = os.getenv("SKILL_GITHUB_E2E_URL", DEFAULT_GITHUB_E2E_URL).strip()
    before = client.get(f"{BASE_URL}/skills", timeout=15).json()
    assert before["code"] == 0
    before_ids = {item["id"] for item in before["data"]["added"]}

    response = client.post(
        f"{BASE_URL}/skills/import/github",
        json={"url": github_url},
        timeout=120,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0, payload
    skill = payload["data"]["skill"]
    assert skill["id"].startswith("skill_github_")
    assert skill["owner_type"] == "personal"
    assert skill["enabled"] is True
    assert skill["name"]
    assert skill["description"]

    after = client.get(f"{BASE_URL}/skills", timeout=15).json()
    assert after["code"] == 0
    after_by_id = {item["id"]: item for item in after["data"]["added"]}
    assert skill["id"] in after_by_id
    assert after_by_id[skill["id"]]["name"] == skill["name"]
    assert skill["id"] not in before_ids or skill["name"] in {
        item["name"] for item in after["data"]["added"]
    }


@pytest.mark.skill_github_e2e
def test_import_skill_from_github_rejects_invalid_url(client):
    if not _backend_ready():
        pytest.skip("Backend not reachable at localhost:8000 with working /skills")

    response = client.post(
        f"{BASE_URL}/skills/import/github",
        json={"url": "https://github.com/acme/nonexistent-repo-404"},
        timeout=120,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == 400
    assert "download" in payload["msg"].lower() or "archive" in payload["msg"].lower()
