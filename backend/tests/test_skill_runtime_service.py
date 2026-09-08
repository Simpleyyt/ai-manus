import pytest

from app.application.services.skill_runtime_service import SkillRuntimeService
from app.application.services.skill_service import SkillService
from app.domain.models.message import Message, RequiredSkill
from app.domain.models.skill import SkillOwnerType, SkillSource, UserSkill
from app.domain.services.prompts.system import format_skill_catalog


class _FakeSkillRepository:
    def __init__(self):
        self.skills = []

    async def save_personal_skill(self, skill):
        self.skills.append(skill)

    async def find_personal_skills_by_user_id(self, user_id):
        return [s for s in self.skills if s.owner_user_id == user_id]

    async def find_personal_skill_by_id_and_user_id(self, skill_id, user_id):
        for skill in self.skills:
            if skill.id == skill_id and skill.owner_user_id == user_id:
                return skill
        return None


class _FakeUserSkillRepository:
    def __init__(self):
        self.items = []

    async def save(self, user_skill):
        self.items = [
            item
            for item in self.items
            if not (
                item.user_id == user_skill.user_id
                and item.skill_id == user_skill.skill_id
            )
        ]
        self.items.append(user_skill)

    async def find_by_user_id(self, user_id):
        return [item for item in self.items if item.user_id == user_id]

    async def find_by_user_id_and_skill_id(self, user_id, skill_id):
        for item in self.items:
            if item.user_id == user_id and item.skill_id == skill_id:
                return item
        return None

    async def count_by_user_id(self, user_id):
        return len([item for item in self.items if item.user_id == user_id])


@pytest.mark.asyncio
async def test_build_skill_catalog_section_lists_enabled_skills(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)

    await service.add_skills("user-1", ["skill_market_research"])
    catalog = await runtime.build_skill_catalog_section("user-1")

    assert "<available_skills>" in catalog
    assert "/market-research" in catalog
    assert "structured brief" in catalog


@pytest.mark.asyncio
async def test_resolve_message_uses_required_skills_structured(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)

    await service.add_skills("user-1", ["skill_market_research"])
    resolved = await runtime.resolve_message(
        "user-1",
        Message(
            message="market-research analyze competitors",
            required_skills=[
                RequiredSkill(skill_id="skill_market_research", name="market-research"),
            ],
        ),
    )

    assert resolved.skill is not None
    assert resolved.message == "analyze competitors"
    assert "structured brief" in resolved.skill.body


@pytest.mark.asyncio
async def test_resolve_message_plain_text_does_not_auto_match_skill(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)

    await service.add_skills("user-1", ["skill_slides"])
    resolved = await runtime.resolve_message(
        "user-1",
        Message(message="做一份 3 页幻灯片，请导出 pptx"),
    )

    assert resolved.skill is None
    assert resolved.message == "做一份 3 页幻灯片，请导出 pptx"


@pytest.mark.asyncio
async def test_resolve_message_ignores_disabled_skill(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)

    await service.add_skills("user-1", ["skill_market_research"])
    await service.set_skill_enabled("user-1", "skill_market_research", False)

    resolved = await runtime.resolve_message(
        "user-1",
        Message(message="/market-research analyze competitors"),
    )

    assert resolved.skill is None
    assert resolved.message == "/market-research analyze competitors"
