import pytest
import tempfile
import os
import io
from unittest.mock import patch, mock_open
from conftest import BASE_URL
import logging
import requests


logger = logging.getLogger(__name__)


@pytest.fixture
def sample_file_content():
    """Create sample file content for testing"""
    return b"This is a test file content for API testing."


@pytest.fixture
def sample_text_file(sample_file_content):
    """Create a temporary text file for testing"""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(sample_file_content)
        f.flush()
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


def test_upload_file_success(client, sample_text_file):
    """Test successful file upload"""
    url = f"{BASE_URL}/files"
    
    with open(sample_text_file, 'rb') as f:
        files = {'file': ('test_file.txt', f, 'text/plain')}
        response = client.post(url, files=files)
    
    logger.info(f"Upload file response: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    assert 'data' in data
    assert 'file_id' in data['data']
    assert data['data']['filename'] == 'test_file.txt'
    assert data['data']['size'] > 0
    assert 'upload_date' in data['data']


def test_upload_file_without_file(client):
    """Test upload without providing file"""
    url = f"{BASE_URL}/files"
    response = client.post(url)
    
    logger.info(f"Upload without file response: {response.status_code} - {response.text}")
    assert response.status_code == 422  # Validation error


def test_upload_empty_file(client):
    """Test upload empty file"""
    url = f"{BASE_URL}/files"
    
    # Create empty file
    empty_file = io.BytesIO(b"")
    files = {'file': ('empty.txt', empty_file, 'text/plain')}
    response = client.post(url, files=files)
    
    logger.info(f"Upload empty file response: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    assert data['data']['size'] == 0


def test_get_file_info_success(client, sample_text_file):
    """Test getting file information"""
    # First upload a file
    upload_url = f"{BASE_URL}/files"
    with open(sample_text_file, 'rb') as f:
        files = {'file': ('info_test.txt', f, 'text/plain')}
        upload_response = client.post(upload_url, files=files)
    
    logger.info(f"Upload for info test response: {upload_response.status_code} - {upload_response.text}")
    file_id = upload_response.json()['data']['file_id']
    
    # Get file info
    info_url = f"{BASE_URL}/files/{file_id}/info"
    response = client.get(info_url)
    
    logger.info(f"Get file info response: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    assert data['data']['file_id'] == file_id
    assert data['data']['filename'] == 'info_test.txt'
    assert data['data']['content_type'] == 'text/plain'
    assert data['data']['size'] > 0
    assert 'upload_date' in data['data']


def test_get_file_info_not_found(client):
    """Test getting info for non-existent file"""
    fake_file_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
    url = f"{BASE_URL}/files/{fake_file_id}/info"
    response = client.get(url)
    
    logger.info(f"Get file info not found response: {response.status_code} - {response.text}")
    assert response.status_code == 404


def test_download_file_success(client, sample_text_file, sample_file_content):
    """Test successful file download"""
    # First upload a file
    upload_url = f"{BASE_URL}/files"
    with open(sample_text_file, 'rb') as f:
        files = {'file': ('download_test.txt', f, 'text/plain')}
        upload_response = client.post(upload_url, files=files)
    
    logger.info(f"Upload for download test response: {upload_response.status_code} - {upload_response.text}")
    file_id = upload_response.json()['data']['file_id']
    
    # Download file
    download_url = f"{BASE_URL}/files/{file_id}"
    response = client.get(download_url)
    
    logger.info(f"Download file response: {response.status_code} - Content length: {len(response.content)}")
    assert response.status_code == 200
    assert response.content == sample_file_content
    assert 'Content-Disposition' in response.headers
    assert 'download_test.txt' in response.headers['Content-Disposition']


def test_download_file_not_found(client):
    """Test downloading non-existent file"""
    fake_file_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
    url = f"{BASE_URL}/files/{fake_file_id}"
    response = client.get(url)
    
    logger.info(f"Download file not found response: {response.status_code} - {response.text}")
    assert response.status_code == 404


def test_delete_file_success(client, sample_text_file):
    """Test successful file deletion"""
    # First upload a file
    upload_url = f"{BASE_URL}/files"
    with open(sample_text_file, 'rb') as f:
        files = {'file': ('delete_test.txt', f, 'text/plain')}
        upload_response = client.post(upload_url, files=files)
    
    file_id = upload_response.json()['data']['file_id']
    
    # Delete file
    delete_url = f"{BASE_URL}/files/{file_id}"
    response = client.delete(delete_url)
    
    logger.info(f"Delete file response: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    
    # Verify file is deleted by trying to get info
    info_url = f"{BASE_URL}/files/{file_id}/info"
    info_response = client.get(info_url)
    logger.info(f"Verify deletion response: {info_response.status_code} - {info_response.text}")
    assert info_response.status_code == 404


def test_delete_file_not_found(client):
    """Test deleting non-existent file"""
    fake_file_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
    url = f"{BASE_URL}/files/{fake_file_id}"
    response = client.delete(url)
    
    logger.info(f"Delete file not found response: {response.status_code} - {response.text}")
    assert response.status_code == 404


def test_upload_large_file(client):
    """Test uploading a larger file"""
    # Create a 1MB file content
    large_content = b"A" * (1024 * 1024)  # 1MB
    
    url = f"{BASE_URL}/files"
    files = {'file': ('large_file.txt', io.BytesIO(large_content), 'text/plain')}
    response = client.post(url, files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    assert data['data']['size'] == 1024 * 1024


def test_upload_binary_file(client):
    """Test uploading a binary file"""
    # Create binary content
    binary_content = bytes(range(256))  # 0-255 bytes
    
    url = f"{BASE_URL}/files"
    files = {'file': ('binary_file.bin', io.BytesIO(binary_content), 'application/octet-stream')}
    response = client.post(url, files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 0
    assert data['data']['size'] == 256
    
    # Download and verify content
    file_id = data['data']['file_id']
    download_url = f"{BASE_URL}/files/{file_id}"
    download_response = client.get(download_url)
    
    assert download_response.status_code == 200
    assert download_response.content == binary_content

