"""Skill catalog and import routes.

Upload (multipart zip/.skill/.md) and GitHub import both store the full package
bytes via ``SkillService.ingest_skill_package`` (not SKILL.md-only).
"""

from fastapi import APIRouter, Depends, File, UploadFile

from app.application.errors.exceptions import NotFoundError
from app.application.services.skill_service import SkillService
from app.domain.models.skill import Skill
from app.domain.models.user import User
from app.interfaces.dependencies import get_current_user, get_skill_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.skill import (
    AddSkillsRequest,
    AddedSkillItem,
    ImportGithubSkillRequest,
    ImportSkillResponse,
    SkillItem,
    SkillsStateResponse,
    UpdateSkillEnabledRequest,
)

router = APIRouter(prefix="/skills", tags=["skills"])


def _to_skill_item(skill: Skill) -> SkillItem:
    return SkillItem(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        owner_type=skill.owner_type.value,
    )


def _to_added_item(skill: Skill, *, enabled: bool) -> AddedSkillItem:
    return AddedSkillItem(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        owner_type=skill.owner_type.value,
        enabled=enabled,
    )


@router.get("", response_model=APIResponse[SkillsStateResponse])
async def get_skills_state(
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> APIResponse[SkillsStateResponse]:
    catalog, added = await skill_service.get_state(current_user.id)
    return APIResponse.success(
        SkillsStateResponse(
            catalog=[_to_skill_item(skill) for skill in catalog],
            added=[
                _to_added_item(skill, enabled=subscription.enabled)
                for skill, subscription in added
            ],
        )
    )


@router.post("/added", response_model=APIResponse[SkillsStateResponse])
async def add_skills(
    request: AddSkillsRequest,
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> APIResponse[SkillsStateResponse]:
    await skill_service.add_skills(current_user.id, request.skill_ids)
    catalog, added = await skill_service.get_state(current_user.id)
    return APIResponse.success(
        SkillsStateResponse(
            catalog=[_to_skill_item(skill) for skill in catalog],
            added=[
                _to_added_item(skill, enabled=subscription.enabled)
                for skill, subscription in added
            ],
        )
    )


@router.patch("/added/{skill_id}", response_model=APIResponse[AddedSkillItem])
async def update_skill_enabled(
    skill_id: str,
    request: UpdateSkillEnabledRequest,
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> APIResponse[AddedSkillItem]:
    subscription = await skill_service.set_skill_enabled(
        current_user.id, skill_id, request.enabled
    )
    catalog, added = await skill_service.get_state(current_user.id)
    for skill, sub in added:
        if sub.skill_id == subscription.skill_id:
            return APIResponse.success(_to_added_item(skill, enabled=sub.enabled))
    raise NotFoundError("Skill not found after update")


@router.post("/import/github", response_model=APIResponse[ImportSkillResponse])
async def import_skill_from_github(
    request: ImportGithubSkillRequest,
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> APIResponse[ImportSkillResponse]:
    skill = await skill_service.import_from_github(current_user.id, request.url)
    return APIResponse.success(
        ImportSkillResponse(skill=_to_added_item(skill, enabled=True))
    )


@router.post("/import/upload", response_model=APIResponse[ImportSkillResponse])
async def import_skill_from_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> APIResponse[ImportSkillResponse]:
    filename = file.filename or ""
    data = await file.read()
    skill = await skill_service.import_from_upload(current_user.id, filename, data)
    return APIResponse.success(
        ImportSkillResponse(skill=_to_added_item(skill, enabled=True))
    )
