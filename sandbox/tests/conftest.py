"""
Pytest configuration and fixtures
"""
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import requests

# Base URL for API testing
BASE_URL = "http://localhost:8080"


@pytest.fixture
def client():
    """Create requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def temp_test_file(client):
    """Create temporary test file inside the sandbox via the file API"""
    temp_file = "/tmp/test_file.txt"

    content = "Line 1: Hello World\nLine 2: This is a test\nLine 3: Python testing"
    client.post(f"{BASE_URL}/api/v1/file/write", json={
        "file": temp_file,
        "content": content
    })

    yield temp_file

    # Cleanup via API
    try:
        client.post(f"{BASE_URL}/api/v1/file/write", json={
            "file": temp_file,
            "content": ""
        })
    except requests.RequestException:
        pass
