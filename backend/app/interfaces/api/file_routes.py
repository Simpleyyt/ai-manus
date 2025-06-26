from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import logging

from app.application.services.file_service import FileService
from app.application.errors.exceptions import NotFoundError
from app.infrastructure.external.file.gridfsfile import GridFSFileStorage
from app.infrastructure.storage.mongodb import get_mongodb
from app.interfaces.schemas.response import (
    APIResponse, FileUploadResponse, FileInfoResponse,
)

logger = logging.getLogger(__name__)

def get_file_service() -> FileService:
    """Create FileService instance with GridFS file storage"""
    file_storage = GridFSFileStorage(mongodb=get_mongodb())
    return FileService(file_storage=file_storage)

router = APIRouter(prefix="/files", tags=["files"])

@router.post("", response_model=APIResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service)
) -> APIResponse[FileUploadResponse]:
    """Upload file"""
    # Upload file
    result = await file_service.upload_file(
        file_data=file.file,
        filename=file.filename,
        content_type=file.content_type
    )
    
    return APIResponse.success(FileUploadResponse(
        file_id=result.file_id,
        filename=result.filename,
        size=result.size,
        upload_date=result.upload_date.isoformat(),
        message="File uploaded successfully"
    ))

@router.get("/{file_id}")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Download file"""
    try:
        file_data, file_info = await file_service.download_file(file_id)
    except FileNotFoundError:
        raise NotFoundError("File not found")
    
    # Encode filename properly for Content-Disposition header
    # Use URL encoding for non-ASCII characters to ensure latin-1 compatibility
    import urllib.parse
    encoded_filename = urllib.parse.quote(file_info.filename, safe='')
    
    headers = {
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    }
    
    return StreamingResponse(
        file_data,
        media_type=file_info.content_type or 'application/octet-stream',
        headers=headers
    )

@router.delete("/{file_id}", response_model=APIResponse[None])
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
) -> APIResponse[None]:
    """Delete file"""
    success = await file_service.delete_file(file_id)
    if not success:
        raise NotFoundError("File not found")
    return APIResponse.success()

@router.get("/{file_id}/info", response_model=APIResponse[FileInfoResponse])
async def get_file_info(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
) -> APIResponse[FileInfoResponse]:
    """Get file information"""
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise NotFoundError("File not found")
    
    return APIResponse.success(FileInfoResponse(
        file_id=file_info.file_id,
        filename=file_info.filename,
        content_type=file_info.content_type,
        size=file_info.size,
        upload_date=file_info.upload_date.isoformat(),
        metadata=file_info.metadata
    ))
