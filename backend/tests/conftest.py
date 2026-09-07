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
    """
    monkeypatch.delenv("API_BASE", raising=False)

@pytest.fixture
def client():
    """Create requests session"""
    session = requests.Session()
    # Don't set default Content-Type to allow multipart/form-data for file uploads
    return session
