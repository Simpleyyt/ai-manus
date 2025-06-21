from typing import Optional, Dict, Any, List, BinaryIO, Union
from datetime import datetime
from pydantic import BaseModel
from io import BytesIO
from fastapi.responses import StreamingResponse


class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str
    filename: str
    content_type: Optional[str] = None
    size: int
    upload_date: datetime
    metadata: Optional[Dict[str, Any]] = None


class FileUploadResult(BaseModel):
    """文件上传结果模型"""
    file_id: str
    filename: str
    size: int
    content_type: Optional[str] = None
    upload_date: datetime
    message: str = "File uploaded successfully"


class FileDownloadResult(BaseModel):
    """文件下载结果模型"""
    file_data: Union[BinaryIO, Any]
    filename: str
    content_type: Optional[str] = None
    size: int
    
    class Config:
        arbitrary_types_allowed = True


class FileListResult(BaseModel):
    """文件列表结果模型"""
    files: List[FileInfo]
    total: int
    limit: int
    skip: int 