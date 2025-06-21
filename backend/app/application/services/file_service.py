from typing import Dict, Any, Optional, BinaryIO
import logging
from app.domain.external.file import FileStorage
from app.domain.models.file import FileUploadResult, FileDownloadResult, FileInfo, FileListResult

# Set up logger
logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, file_storage: Optional[FileStorage] = None):
        self._file_storage = file_storage

    async def upload_file(self, file_data: BinaryIO, filename: str, content_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> FileUploadResult:
        """Upload file"""
        if not self._file_storage:
            raise RuntimeError("File storage service not available")
        return await self._file_storage.upload_file(file_data, filename, content_type, metadata)
    
    async def download_file(self, file_id: str) -> FileDownloadResult:
        """Download file"""
        if not self._file_storage:
            raise RuntimeError("File storage service not available")
        return await self._file_storage.download_file(file_id)

    async def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        if not self._file_storage:
            raise RuntimeError("File storage service not available")
        return await self._file_storage.delete_file(file_id)

    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """Get file information"""
        if not self._file_storage:
            raise RuntimeError("File storage service not available")
        return await self._file_storage.get_file_info(file_id)
