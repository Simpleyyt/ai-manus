from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CreateProjectRequest(BaseModel):
    name: str
    instruction: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    instruction: Optional[str] = None


class ProjectItem(BaseModel):
    project_id: str
    name: str
    instruction: Optional[str] = None
    is_pinned: bool = False
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ListProjectsResponse(BaseModel):
    projects: List[ProjectItem]


class PinProjectRequest(BaseModel):
    is_pinned: bool = True
