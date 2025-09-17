from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class FileInfo(BaseModel):
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    upload_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    file_url: Optional[str] = None
