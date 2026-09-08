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

@pytest.fixture
def client():
    """Create requests session"""
    session = requests.Session()
    # Don't set default Content-Type to allow multipart/form-data for file uploads
    return session
