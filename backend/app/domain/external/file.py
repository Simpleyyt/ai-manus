from typing import Protocol, BinaryIO, Optional, Dict, Any, Tuple
from app.domain.models.file import FileInfo

class FileStorage(Protocol):
    """File storage service interface for file upload and download operations"""
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Upload file to storage
        
        Args:
            file_data: Binary file data stream
            filename: Name of the file to be stored
            user_id: ID of the user uploading the file
            content_type: MIME type of the file (optional)
            metadata: Additional metadata to store with the file (optional)
            
        Returns:
            FileUploadResult containing file_id and upload information
        """
        ...
    
    async def download_file(
        self,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Tuple[BinaryIO, FileInfo]:
        """Download file from storage by file ID
        
        Args:
            file_id: File ID
            user_id: ID of the user downloading the file (optional, if None skips access control)
            
        Returns:
            FileDownloadResult containing file data and metadata for FastAPI streaming
        """
        ...
    

    
    async def delete_file(
        self,
        file_id: str,
        user_id: str
    ) -> bool:
        """Delete file from storage
        
        Args:
            file_id: File ID
            user_id: ID of the user deleting the file
            
        Returns:
            True if deletion successful, False otherwise
        """
        ...
    
    async def get_file_info(
        self,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Optional[FileInfo]:
        """Get file metadata from storage
        
        Args:
            file_id: File ID
            user_id: ID of the user requesting file info
            
        Returns:
            FileInfo containing file metadata, None if file not found
        """
        ...

