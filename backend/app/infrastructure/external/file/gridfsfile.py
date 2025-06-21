import logging
from typing import BinaryIO, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from gridfs.errors import NoFile
from pymongo.errors import PyMongoError
import io

from app.domain.external.file import FileStorage
from app.domain.models.file import FileUploadResult, FileDownloadResult, FileInfo, FileListResult
from app.infrastructure.storage.mongodb import MongoDB
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class GridFSFileStorage(FileStorage):
    """基于 MongoDB GridFS 的文件存储实现"""
    
    def __init__(self, mongodb: MongoDB, bucket_name: str = "fs"):
        """
        初始化 GridFS 文件存储
        
        Args:
            mongodb: MongoDB 连接实例
            bucket_name: GridFS bucket 名称，默认为 'fs'
        """
        self.mongodb = mongodb
        self.bucket_name = bucket_name
        self.settings = get_settings()
    
    def _get_gridfs_bucket(self) -> AsyncIOMotorGridFSBucket:
        """获取异步 GridFS Bucket 实例"""
        if not self.mongodb.client:
            raise RuntimeError("MongoDB client not initialized")
        
        # 使用配置中的数据库名称
        database = self.mongodb.client[self.settings.mongodb_database]
        return AsyncIOMotorGridFSBucket(database, bucket_name=self.bucket_name)
    
    def _get_files_collection(self):
        """获取 files 集合，用于查询文件元数据"""
        if not self.mongodb.client:
            raise RuntimeError("MongoDB client not initialized")
        
        database = self.mongodb.client[self.settings.mongodb_database]
        return database[f"{self.bucket_name}.files"]
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileUploadResult:
        """上传文件到 GridFS"""
        try:
            bucket = self._get_gridfs_bucket()
            
            # 准备元数据
            file_metadata = {
                'filename': filename,
                'uploadDate': datetime.utcnow(),
                **(metadata or {})
            }
            
            if content_type:
                file_metadata['contentType'] = content_type
            
            # 直接使用文件流上传，避免将整个文件读取到内存
            file_id = await bucket.upload_from_stream(
                filename,
                file_data,
                metadata=file_metadata
            )
            
            # 获取文件大小（如果需要的话，可以从GridFS中获取）
            files_collection = self._get_files_collection()
            file_info = await files_collection.find_one({"_id": file_id})
            file_size = file_info.get('length', 0) if file_info else 0
            
            logger.info(f"File uploaded successfully: {filename} (ID: {file_id})")
            
            return FileUploadResult(
                file_id=str(file_id),
                filename=filename,
                size=file_size,
                content_type=content_type,
                upload_date=file_metadata['uploadDate']
            )
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}")
            raise
    
    async def download_file(self, file_id: str) -> FileDownloadResult:
        """通过文件 ID 下载文件"""
        try:
            bucket = self._get_gridfs_bucket()
            files_collection = self._get_files_collection()
            
            # 转换 ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # 获取文件信息
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                raise FileNotFoundError(f"File not found with ID: {file_id}")
            
            download_stream = await bucket.open_download_stream(obj_id)
            
            return FileDownloadResult(
                file_data=download_stream,
                filename=file_info.get('filename', f"file_{file_id}"),
                content_type=file_info.get('metadata', {}).get('contentType'),
                size=file_info.get('length', 0)
            )
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        try:
            bucket = self._get_gridfs_bucket()
            files_collection = self._get_files_collection()
            
            # 转换 ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # 检查文件是否存在
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                return False
            
            # 删除文件
            await bucket.delete(obj_id)
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}")
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        try:
            files_collection = self._get_files_collection()
            
            # 转换 ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                raise ValueError(f"Invalid file ID format: {file_id}")
            
            # 获取文件信息
            file_info = await files_collection.find_one({"_id": obj_id})
            if not file_info:
                return None
            
            return FileInfo(
                file_id=str(file_info['_id']),
                filename=file_info.get('filename', f"file_{file_id}"),
                content_type=file_info.get('metadata', {}).get('contentType'),
                size=file_info.get('length', 0),
                upload_date=file_info.get('uploadDate', datetime.utcnow()),
                metadata=file_info.get('metadata')
            )
            
        except Exception as e:
            logger.error(f"Failed to get file info {file_id}: {str(e)}")
            return None
    
    async def list_files(
        self,
        limit: int = 50,
        skip: int = 0,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> FileListResult:
        """列出文件"""
        try:
            files_collection = self._get_files_collection()
            
            # 构建查询条件
            query = filter_criteria or {}
            
            # 获取文件列表
            cursor = files_collection.find(query).sort("uploadDate", -1).skip(skip).limit(limit)
            file_docs = await cursor.to_list(length=limit)
            
            files = []
            for file_doc in file_docs:
                files.append(FileInfo(
                    file_id=str(file_doc['_id']),
                    filename=file_doc.get('filename', f"file_{file_doc['_id']}"),
                    content_type=file_doc.get('metadata', {}).get('contentType'),
                    size=file_doc.get('length', 0),
                    upload_date=file_doc.get('uploadDate', datetime.utcnow()),
                    metadata=file_doc.get('metadata')
                ))
            
            # 获取总数
            total = await files_collection.count_documents(query)
            
            return FileListResult(
                files=files,
                total=total,
                limit=limit,
                skip=skip
            )
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise
    
    async def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        try:
            files_collection = self._get_files_collection()
            
            # 转换 ObjectId
            try:
                obj_id = ObjectId(file_id)
            except Exception:
                return False
            
            file_info = await files_collection.find_one({"_id": obj_id})
            return file_info is not None
            
        except Exception as e:
            logger.error(f"Failed to check file existence {file_id}: {str(e)}")
            return False 