"""
Integration tests for sandbox file upload and download functionality
"""
import logging
import pytest
import tempfile
import os
import io

from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


@pytest.fixture
def sandbox_instance():
    """Create a DockerSandbox instance for testing"""
    # Use localhost for testing (assumes sandbox is running locally)
    return DockerSandbox(ip="127.0.0.1", container_name="test-sandbox")


@pytest.fixture
def sample_file_content():
    """Create sample file content for testing"""
    return b"This is a test file content for sandbox testing."


@pytest.fixture
def sample_binary_stream(sample_file_content):
    """Create a binary stream from sample content"""
    return io.BytesIO(sample_file_content)


@pytest.fixture
def temp_file_path():
    """Generate a temporary file path for testing"""
    return f"/tmp/test_file_{os.urandom(8).hex()}.txt"


# Upload Tests

async def test_file_upload_success(sandbox_instance, sample_binary_stream, temp_file_path):
    """Test successful file upload to sandbox"""
    result = await sandbox_instance.file_upload(
        file_data=sample_binary_stream,
        path=temp_file_path,
        filename="test_file.txt"
    )

    # Verify result
    assert isinstance(result, ToolResult)
    assert result.success is True
    assert "successfully" in result.message.lower()


async def test_file_upload_without_filename(sandbox_instance, sample_binary_stream, temp_file_path):
    """Test file upload without specifying filename"""
    result = await sandbox_instance.file_upload(
        file_data=sample_binary_stream,
        path=temp_file_path
    )

    # Verify result
    assert isinstance(result, ToolResult)
    assert result.success is True


async def test_file_upload_large_file(sandbox_instance, temp_file_path):
    """Test uploading a large file"""
    # Create large content (1MB)
    large_content = b"A" * (1024 * 1024)
    large_stream = io.BytesIO(large_content)

    result = await sandbox_instance.file_upload(
        file_data=large_stream,
        path=temp_file_path,
        filename="large_file.bin"
    )

    # Verify result
    assert isinstance(result, ToolResult)
    assert result.success is True


async def test_file_upload_empty_file(sandbox_instance, temp_file_path):
    """Test uploading an empty file"""
    empty_stream = io.BytesIO(b"")

    result = await sandbox_instance.file_upload(
        file_data=empty_stream,
        path=temp_file_path,
        filename="empty_file.txt"
    )

    # Verify result
    assert isinstance(result, ToolResult)
    assert result.success is True


# Download Tests

async def test_file_download_success(sandbox_instance, sample_binary_stream, sample_file_content, temp_file_path):
    """Test successful file download from sandbox"""
    # First upload a file
    upload_result = await sandbox_instance.file_upload(
        file_data=sample_binary_stream,
        path=temp_file_path,
        filename="download_test.txt"
    )
    logger.info(f"Upload for download test response: {upload_result.success} - {upload_result.message}")
    assert upload_result.success is True

    # Then download it
    result = await sandbox_instance.file_download(temp_file_path)

    # Verify result
    content = result.read()
    assert content == sample_file_content

    # Reset stream position and verify we can read again
    result.seek(0)
    content_again = result.read()
    assert content_again == sample_file_content


async def test_file_download_nonexistent_file(sandbox_instance):
    """Test downloading a file that does not exist"""
    nonexistent_path = f"/tmp/nonexistent_{os.urandom(8).hex()}.txt"

    # This should raise an exception or return an error
    with pytest.raises(Exception):
        await sandbox_instance.file_download(nonexistent_path)


async def test_file_download_empty_file(sandbox_instance, temp_file_path):
    """Test downloading an empty file"""
    # Upload empty file first
    empty_stream = io.BytesIO(b"")
    upload_result = await sandbox_instance.file_upload(
        file_data=empty_stream,
        path=temp_file_path,
        filename="empty.txt"
    )
    assert upload_result.success is True

    # Download the empty file
    result = await sandbox_instance.file_download(temp_file_path)

    # Verify result
    content = result.read()
    assert content == b""


async def test_file_download_large_file(sandbox_instance, temp_file_path):
    """Test downloading a large file"""
    # Create and upload large content (1MB)
    large_content = b"B" * (1024 * 1024)
    large_stream = io.BytesIO(large_content)

    upload_result = await sandbox_instance.file_upload(
        file_data=large_stream,
        path=temp_file_path,
        filename="large_download.bin"
    )
    assert upload_result.success is True

    # Download the large file
    result = await sandbox_instance.file_download(temp_file_path)

    # Verify result
    content = result.read()
    assert content == large_content
    assert len(content) == 1024 * 1024


# Integration Tests

async def test_upload_then_download_cycle(sandbox_instance, sample_file_content, temp_file_path):
    """Test uploading a file and then downloading it"""
    sample_stream = io.BytesIO(sample_file_content)

    # Upload file
    upload_result = await sandbox_instance.file_upload(
        file_data=sample_stream,
        path=temp_file_path,
        filename="cycle_test.txt"
    )

    # Verify upload success
    assert upload_result.success is True

    # Download file
    download_result = await sandbox_instance.file_download(temp_file_path)

    # Verify download result matches original content
    downloaded_content = download_result.read()
    assert downloaded_content == sample_file_content


async def test_multiple_file_operations(sandbox_instance, temp_file_path):
    """Test multiple file upload and download operations"""
    # Test data for multiple files
    files_data = [
        (b"Content of file 1", "file1.txt"),
        (b"Content of file 2", "file2.txt"),
        (b"Content of file 3", "file3.txt"),
    ]

    uploaded_paths = []

    # Upload multiple files
    for i, (content, filename) in enumerate(files_data):
        file_path = f"{temp_file_path}_{i}"
        stream = io.BytesIO(content)
        
        upload_result = await sandbox_instance.file_upload(
            file_data=stream,
            path=file_path,
            filename=filename
        )
        
        assert upload_result.success is True
        uploaded_paths.append((file_path, content))

    # Download and verify all files
    for file_path, expected_content in uploaded_paths:
        download_result = await sandbox_instance.file_download(file_path)
        downloaded_content = download_result.read()
        assert downloaded_content == expected_content


async def test_file_overwrite(sandbox_instance, temp_file_path):
    """Test overwriting an existing file"""
    # Upload initial file
    initial_content = b"Initial content"
    initial_stream = io.BytesIO(initial_content)
    
    upload_result1 = await sandbox_instance.file_upload(
        file_data=initial_stream,
        path=temp_file_path,
        filename="overwrite_test.txt"
    )
    assert upload_result1.success is True

    # Upload new content to same path
    new_content = b"New content that overwrites the old one"
    new_stream = io.BytesIO(new_content)
    
    upload_result2 = await sandbox_instance.file_upload(
        file_data=new_stream,
        path=temp_file_path,
        filename="overwrite_test.txt"
    )
    assert upload_result2.success is True

    # Download and verify new content
    download_result = await sandbox_instance.file_download(temp_file_path)
    downloaded_content = download_result.read()
    assert downloaded_content == new_content
    assert downloaded_content != initial_content 