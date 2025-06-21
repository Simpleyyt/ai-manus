import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from conftest import BASE_URL
import logging


logger = logging.getLogger(__name__)


@pytest.mark.file_api
def test_upload_file_success(client):
    """Test successful file upload"""
    temp_path = "resource/test_upload_unique.txt"  # Use unique filename
    
    # Create test file content
    test_content = b"This is test upload content"
    
    # For file upload, create a new requests session without JSON headers
    import requests
    upload_client = requests.Session()
    
    response = upload_client.post(
        f"{BASE_URL}/api/v1/file/upload",
        files={"file": ("test.txt", test_content, "text/plain")},
        data={"path": temp_path}
    )
    
    assert response.status_code == 200
    data = response.json()

    logger.info(f"Upload response: {data}")

    assert data["success"] is True
    assert "File uploaded successfully" in data["message"]
    
    # Verify file was created via API
    read_response = client.post(f"{BASE_URL}/api/v1/file/read", json={
        "file": temp_path
    })
    read_data = read_response.json()
    logger.info(f"Read response: {read_data}")
    assert read_response.status_code == 200
    assert read_data["data"]["content"] == test_content.decode()


@pytest.mark.file_api
def test_download_file_success(client, temp_test_file):
    """Test successful file download"""
    response = client.get(f"{BASE_URL}/api/v1/file/download", params={"path": temp_test_file})
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers.get("content-disposition", "")


@pytest.mark.file_api
def test_download_nonexistent_file(client):
    """Test downloading non-existent file"""
    response = client.get(f"{BASE_URL}/api/v1/file/download", params={"path": "1nonexistent.txt"})

    logger.info(f"Download response: {response.status_code}")
    
    assert response.status_code == 404 or response.status_code == 500
