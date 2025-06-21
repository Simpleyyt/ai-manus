"""
File operation API interfaces
"""
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.schemas.file import (
    FileReadRequest, FileWriteRequest, FileReplaceRequest,
    FileSearchRequest, FileFindRequest
)
from app.schemas.response import Response
from app.services.file import file_service

router = APIRouter()

@router.post("/read", response_model=Response)
async def read_file(request: FileReadRequest):
    """
    Read file content
    """
    result = await file_service.read_file(
        file=request.file,
        start_line=request.start_line,
        end_line=request.end_line,
        sudo=request.sudo
    )
    
    # Construct response
    return Response(
        success=True,
        message="File read successfully",
        data=result.model_dump()
    )

@router.post("/write", response_model=Response)
async def write_file(request: FileWriteRequest):
    """
    Write file content
    """
    result = await file_service.write_file(
        file=request.file,
        content=request.content,
        append=request.append,
        leading_newline=request.leading_newline,
        trailing_newline=request.trailing_newline,
        sudo=request.sudo
    )
    
    # Construct response
    return Response(
        success=True,
        message="File written successfully",
        data=result.model_dump()
    )

@router.post("/replace", response_model=Response)
async def replace_in_file(request: FileReplaceRequest):
    """
    Replace string in file
    """
    result = await file_service.str_replace(
        file=request.file,
        old_str=request.old_str,
        new_str=request.new_str,
        sudo=request.sudo
    )
    
    # Construct response
    return Response(
        success=True,
        message=f"Replacement completed, replaced {result.replaced_count} occurrences",
        data=result.model_dump()
    )

@router.post("/search", response_model=Response)
async def search_in_file(request: FileSearchRequest):
    """
    Search in file content
    """
    result = await file_service.find_in_content(
        file=request.file,
        regex=request.regex,
        sudo=request.sudo
    )
    
    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.matches)} matches",
        data=result.model_dump()
    )

@router.post("/find", response_model=Response)
async def find_files(request: FileFindRequest):
    """
    Find files by name pattern
    """
    result = await file_service.find_by_name(
        path=request.path,
        glob_pattern=request.glob
    )
    
    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.files)} files",
        data=result.model_dump()
    )

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form(None)
):
    """
    Upload file using streaming
    """
    if not path:
        path = f"/tmp/{file.filename}"
    
    result = await file_service.upload_file(
        path=path,
        file_stream=file
    )
    
    return Response(
        success=True,
        message="File uploaded successfully",
        data=result.model_dump()
    )

@router.get("/download")
async def download_file(path: str):
    """
    Download file using FileResponse
    """
    # Check if file exists (this will raise appropriate exception if not found)
    file_service.ensure_file(path)
    
    # Determine filename from path
    filename = path.split('/')[-1]
    
    return FileResponse(
        path=path,
        filename=filename,
        media_type='application/octet-stream'
    )
