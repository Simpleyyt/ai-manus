import logging
import io
from typing import BinaryIO, Optional, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.domain.external.file import FileStorage
from app.domain.models.file import FileInfo
from app.infrastructure.storage.mongodb import MongoDB
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class GridFSFileStorage(FileStorage):
    """MongoDB GridFS-based file storage implementation"""
    
    def __init__(self, mongodb: MongoDB, bucket_name: str = "fs"):
        """
        Initialize GridFS file storage
        
        Args:
            mongodb: MongoDB connection instance
            bucket_name: GridFS bucket name, default is 'fs'
        """
        self.mongodb = mongodb
        self.bucket_name = bucket_name
        self.settings = get_settings()
    
    def _get_gridfs_bucket(self) -> AsyncIOMotorGridFSBucket:
        """Get async GridFS Bucket instance"""
        if not self.mongodb.client:
            raise RuntimeError("MongoDB client not initialized")
        
        # Use database name from configuration
        database = self.mongodb.client[self.settings.mongodb_database]
        return AsyncIOMotorGridFSBucket(database, bucket_name=self.bucket_name)
    
    def _get_files_collection(self):
        """Get files collection for querying file metadata"""
        if not self.mongodb.client:
            raise RuntimeError("MongoDB client not initialized")
        
        database = self.mongodb.client[self.settings.mongodb_database]
        return database[f"{self.bucket_name}.files"]
    
    def _create_file_info(self, file_info: Dict[str, Any], file_id: str) -> FileInfo:
        """Create FileInfo object from GridFS file metadata"""
        return FileInfo(
            file_id=str(file_info['_id']),
            filename=file_info.get('filename', f"file_{file_id}"),
            content_type=file_info.get('metadata', {}).get('contentType'),
            size=file_info.get('length', 0),
            upload_date=file_info.get('uploadDate', datetime.utcnow()),
            metadata=file_info.get('metadata')
        )
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Upload file to GridFS"""
        try:
            bucket = self._get_gridfs_bucket()
            
            # Prepare metadata
            file_metadata = {
                'filename': filename,
                'uploadDate': datetime.utcnow(),
                **(metadata or {})
            }
            
            if content_type:
                file_metadata['contentType'] = content_type
            
            # Upload directly from file stream to avoid loading entire file into memory
            file_id = await bucket.upload_from_stream(
                filename,
                file_data,
                metadata=file_metadata
            )
            
            # Get file size (can be retrieved from GridFS if needed)
            files_collection = self._get_files_collection()
            file_info = await files_collection.find_one({"_id": file_id})
            file_size = file_info.get('length', 0) if file_info else 0
            
            logger.info(f"File uploaded successfully: {filename} (ID: {file_id})")
            
            return FileInfo(
                file_id=str(file_id),
                filename=filename,
                size=file_size,
                content_type=content_type,
                upload_date=file_metadata['uploadDate'],
                metadata=file_metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}")
            raise
    
    async def download_file(self, file_id: str) -> Tuple[BinaryIO, FileInfo]:
        """Download file by file ID"""
        try:
            bucket = self._get_gridfs_bucket()
            files_collection = self._get_files_collection()
            
            # Convert ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # Get file information
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                raise FileNotFoundError(f"File not found with ID: {file_id}")
            stream = io.BytesIO()
            await bucket.download_to_stream(obj_id, stream)
            stream.seek(0)
            return stream, self._create_file_info(file_info, file_id)
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        try:
            bucket = self._get_gridfs_bucket()
            files_collection = self._get_files_collection()
            
            # Convert ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # Check if file exists
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                return False
            
            # Delete file
            await bucket.delete(obj_id)
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}")
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """Get file information"""
        try:
            files_collection = self._get_files_collection()
            
            # Convert ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # Get file information
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                return None
            
            return self._create_file_info(file_info, file_id)
            
        except Exception as e:
            logger.error(f"Failed to get file info {file_id}: {str(e)}")
            return None
