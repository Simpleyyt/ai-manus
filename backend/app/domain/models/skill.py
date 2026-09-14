from datetime import UTC, datetime
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class SkillOwnerType(str, Enum):
    OFFICIAL = "official"
    PERSONAL = "personal"


class SkillSource(str, Enum):
    CATALOG = "catalog"
    GITHUB = "github"
    UPLOAD = "upload"


class Skill(BaseModel):
    id: str
    name: str
    description: str
    body: Optional[str] = None
    owner_type: SkillOwnerType
    owner_user_id: Optional[str] = None
    source: SkillSource = SkillSource.CATALOG
    source_url: Optional[str] = None
    package_file_id: Optional[str] = None
    package_sha256: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserSkill(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str
    skill_id: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
