import io
from datetime import UTC, datetime

import pytest


class FakeFileStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}

    async def upload_file(
        self,
        file_data,
        filename,
        user_id,
        content_type=None,
        metadata=None,
    ):
        from app.domain.models.file import FileInfo

        data = file_data.read()
        file_id = f"file_{len(self.files) + 1}"
        self.files[file_id] = data
        return FileInfo(
            file_id=file_id,
            filename=filename,
            size=len(data),
            upload_date=datetime.now(UTC),
        )

    async def download_file(self, file_id, user_id=None):
        from app.domain.models.file import FileInfo

        data = self.files[file_id]
        return io.BytesIO(data), FileInfo(
            file_id=file_id,
            filename="skill.zip",
            size=len(data),
            upload_date=datetime.now(UTC),
        )


@pytest.fixture
def fake_file_storage():
    return FakeFileStorage()
"""
Pytest configuration and fixtures
"""
import sys
import os
import pytest
import tempfile
from pathlib import Path

# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

# Base URL for API testing
BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture(autouse=True)
def _isolate_llm_env(monkeypatch):
    """Keep offline tests deterministic regardless of the host environment.

    Two leak paths exist: the shell may carry a real API_BASE, and importing
    browser_use (pulled in transitively at collection time) runs load_dotenv,
    which walks up to the repo-root .env and injects API_BASE into the
    process. Settings() would then pick it up and break provider-default
    assertions depending on test order.

    delenv is not enough: pydantic-settings still reads env_file=".env"
    (cwd is backend/ during pytest), so a local API_BASE=mockserver leaks
    into Settings() after the env var is removed. An empty env var beats
    dotenv (env_settings > dotenv_settings) and is falsy for
    ``api_base or ORCAROUTER_API_BASE``.
    """
    monkeypatch.setenv("API_BASE", "")

@pytest.fixture
def client():
    """Create requests session"""
    session = requests.Session()
    # Don't set default Content-Type to allow multipart/form-data for file uploads
    return session
