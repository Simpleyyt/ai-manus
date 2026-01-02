"""
Pytest configuration and fixtures
"""
import sys
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Mock problematic MCP modules before any imports
mcp_mock = MagicMock()
sys.modules['mcp'] = mcp_mock
sys.modules['mcp.client'] = MagicMock()
sys.modules['mcp.client.streamable_http'] = MagicMock()
sys.modules['mcp.client.stdio'] = MagicMock()
sys.modules['mcp.client.sse'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()

# Create mock classes for MCP
mcp_mock.ClientSession = MagicMock()
mcp_mock.StdioServerParameters = MagicMock()

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
