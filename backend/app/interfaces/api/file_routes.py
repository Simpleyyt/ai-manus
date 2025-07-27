from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import logging

from app.application.services.file_service import FileService
from app.application.services.token_service import TokenService
from app.application.errors.exceptions import NotFoundError, UnauthorizedError
from app.interfaces.dependencies import get_file_service, get_current_user, get_token_service, get_optional_current_user
from app.domain.models.user import User
from app.interfaces.schemas.response import (
    APIResponse, FileUploadResponse, FileInfoResponse, SignedUrlResponse
)
from app.interfaces.schemas.request import AccessTokenRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

@router.post("", response_model=APIResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user)
) -> APIResponse[FileUploadResponse]:
    """Upload file"""
    # Upload file
    result = await file_service.upload_file(
        file_data=file.file,
        filename=file.filename,
        user_id=current_user.id,
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
    file_service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_optional_current_user)
):
    """Download file with optional access token"""
    
    # Download file (authentication is handled by middleware for non-token requests)
    try:
        file_data, file_info = await file_service.download_file(file_id, current_user.id if current_user else None)
    except FileNotFoundError:
        raise NotFoundError("File not found")
    except PermissionError:
        raise NotFoundError("File not found")  # Don't reveal if file exists but user has no access
    
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
    file_service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user)
) -> APIResponse[None]:
    """Delete file"""
    success = await file_service.delete_file(file_id, current_user.id)
    if not success:
        raise NotFoundError("File not found")
    return APIResponse.success()

@router.get("/{file_id}/info", response_model=APIResponse[FileInfoResponse])
async def get_file_info(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user)
) -> APIResponse[FileInfoResponse]:
    """Get file information"""
    file_info = await file_service.get_file_info(file_id, current_user.id)
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


@router.post("/{file_id}/signed-url", response_model=APIResponse[SignedUrlResponse])
async def create_file_signed_url(
    file_id: str,
    request_data: AccessTokenRequest,
    current_user: User = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
    token_service: TokenService = Depends(get_token_service)
) -> APIResponse[SignedUrlResponse]:
    """Generate signed URL for file download
    
    This endpoint creates a signed URL that allows temporary access to download
    a specific file without requiring authentication headers.
    """
    
    # Validate expiration time (max 15 minutes)
    expire_minutes = request_data.expire_minutes
    if expire_minutes > 15:
        expire_minutes = 15
    
    # Check if file exists and user has access
    file_info = await file_service.get_file_info(file_id, current_user.id)
    if not file_info:
        raise NotFoundError("File not found")
    
    # Create signed URL for file download
    base_url = f"/api/v1/files/{file_id}"
    signed_url = token_service.create_signed_url(
        base_url=base_url,
        expire_minutes=expire_minutes
    )
    
    logger.info(f"Created signed URL for file download for user {current_user.id}, file {file_id}")
    
    return APIResponse.success(SignedUrlResponse(
        signed_url=signed_url,
        expires_in=expire_minutes * 60,
    ))
