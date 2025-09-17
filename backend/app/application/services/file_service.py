from typing import Dict, Any, Optional, BinaryIO, Tuple
import logging
from app.domain.external.file import FileStorage
from app.domain.models.file import FileInfo
from app.application.services.token_service import TokenService

# Set up logger
logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, file_storage: Optional[FileStorage] = None, token_service: Optional[TokenService] = None):
        self._file_storage = file_storage
        self._token_service = token_service

    async def upload_file(self, file_data: BinaryIO, filename: str, user_id: str, content_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> FileInfo:
        """Upload file"""
        logger.info(f"Upload file request: filename={filename}, user_id={user_id}, content_type={content_type}")
        if not self._file_storage:
            logger.error("File storage service not available")
            raise RuntimeError("File storage service not available")
        
        try:
            result = await self._file_storage.upload_file(file_data, filename, user_id, content_type, metadata)
            logger.info(f"File uploaded successfully: file_id={result.file_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to upload file for user {user_id}: {str(e)}")
            raise
    
    async def download_file(self, file_id: str, user_id: Optional[str] = None) -> Tuple[BinaryIO, FileInfo]:
        """Download file"""
        logger.info(f"Download file request: file_id={file_id}, user_id={user_id}")
        if not self._file_storage:
            logger.error("File storage service not available")
            raise RuntimeError("File storage service not available")
        
        try:
            result = await self._file_storage.download_file(file_id, user_id)
            logger.info(f"File downloaded successfully: file_id={file_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to download file {file_id} for user {user_id}: {str(e)}")
            raise

    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete file"""
        logger.info(f"Delete file request: file_id={file_id}, user_id={user_id}")
        if not self._file_storage:
            logger.error("File storage service not available")
            raise RuntimeError("File storage service not available")
        
        try:
            result = await self._file_storage.delete_file(file_id, user_id)
            if result:
                logger.info(f"File deleted successfully: file_id={file_id}, user_id={user_id}")
            else:
                logger.warning(f"File deletion failed or file not found: file_id={file_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete file {file_id} for user {user_id}: {str(e)}")
            raise

    async def get_file_info(self, file_id: str, user_id: Optional[str] = None) -> Optional[FileInfo]:
        """Get file information"""
        logger.info(f"Get file info request: file_id={file_id}, user_id={user_id}")
        if not self._file_storage:
            logger.error("File storage service not available")
            raise RuntimeError("File storage service not available")
        
        try:
            result = await self._file_storage.get_file_info(file_id, user_id)
            if result:
                logger.info(f"File info retrieved successfully: file_id={file_id}, user_id={user_id}")
            else:
                logger.warning(f"File not found or access denied: file_id={file_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get file info {file_id} for user {user_id}: {str(e)}")
            raise
    
    async def enrich_with_file_url(self, file_info: FileInfo) -> FileInfo:
        """Enrich file information with file URL"""
        logger.info(f"Enrich file info request: file_info={file_info}")
        
        try:
            signed_url = await self.create_signed_url(file_info.file_id, file_info.user_id)
            file_info.file_url = signed_url
            return file_info
        except Exception as e:
            logger.error(f"Failed to enrich file info {file_info.file_id} with file URL: {str(e)}")
            raise

    async def create_signed_url(self, file_id: str, user_id: Optional[str] = None, expire_minutes: int = 30) -> str:
        """Create signed URL for file download"""
        logger.info(f"Create signed URL request: file_id={file_id}, user_id={user_id}, expire_minutes={expire_minutes}")
        
        if not self._token_service:
            logger.error("Token service not available")
            raise RuntimeError("Token service not available")
        
        # Validate expiration time (max 15 minutes)
        if expire_minutes > 30:
            expire_minutes = 30
        
        # Check if file exists and user has access
        file_info = await self.get_file_info(file_id, user_id)
        if not file_info:
            logger.warning(f"File not found or access denied for signed URL: file_id={file_id}, user_id={user_id}")
            raise FileNotFoundError("File not found")
        
        # Create signed URL for file download
        base_url = f"/api/v1/files/{file_id}"
        signed_url = self._token_service.create_signed_url(
            base_url=base_url,
            expire_minutes=expire_minutes
        )
        
        logger.info(f"Created signed URL for file download for user {user_id}, file {file_id}")
        
        return signed_url
