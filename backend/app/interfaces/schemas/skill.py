from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SkillItem(BaseModel):
    id: str
    name: str
    description: str
    owner_type: str


class AddedSkillItem(SkillItem):
    enabled: bool = True


class SkillsStateResponse(BaseModel):
    catalog: List[SkillItem]
    added: List[AddedSkillItem]


class AddSkillsRequest(BaseModel):
    skill_ids: List[str] = Field(min_length=1)


class UpdateSkillEnabledRequest(BaseModel):
    enabled: bool


class ImportGithubSkillRequest(BaseModel):
    url: str


class ImportSkillResponse(BaseModel):
    skill: AddedSkillItem
