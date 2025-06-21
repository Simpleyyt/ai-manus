from typing import Protocol, BinaryIO, Optional, Dict, Any
from app.domain.models.file import FileUploadResult, FileDownloadResult, FileInfo, FileListResult

class FileStorage(Protocol):
    """File storage service interface for file upload and download operations"""
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileUploadResult:
        """Upload file to storage
        
        Args:
            file_data: Binary file data stream
            filename: Name of the file to be stored
            content_type: MIME type of the file (optional)
            metadata: Additional metadata to store with the file (optional)
            
        Returns:
            FileUploadResult containing file_id and upload information
        """
        ...
    
    async def download_file(
        self,
        file_id: str
    ) -> FileDownloadResult:
        """Download file from storage by file ID
        
        Args:
            file_id: File ID
            
        Returns:
            FileDownloadResult containing file data and metadata for FastAPI streaming
        """
        ...
    

    
    async def delete_file(
        self,
        file_id: str
    ) -> bool:
        """Delete file from storage
        
        Args:
            file_id: File ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        ...
    
    async def get_file_info(
        self,
        file_id: str
    ) -> Optional[FileInfo]:
        """Get file metadata from storage
        
        Args:
            file_id: File ID
            
        Returns:
            FileInfo containing file metadata, None if file not found
        """
        ...
    
    async def list_files(
        self,
        limit: int = 50,
        skip: int = 0,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> FileListResult:
        """List files in storage
        
        Args:
            limit: Maximum number of files to return
            skip: Number of files to skip
            filter_criteria: Optional filter criteria for file search
            
        Returns:
            FileListResult containing list of file metadata and total count
        """
        ...
    
    async def file_exists(
        self,
        file_id: str
    ) -> bool:
        """Check if file exists in storage
        
        Args:
            file_id: File ID
            
        Returns:
            True if file exists, False otherwise
        """
        ... 