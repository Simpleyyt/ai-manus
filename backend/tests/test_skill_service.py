import io
import zipfile
from unittest.mock import AsyncMock

import pytest

from app.application.services.skill_service import SkillService
from app.domain.models.skill import SkillOwnerType, SkillSource


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
        self.items = [item for item in self.items if not (
            item.user_id == user_skill.user_id and item.skill_id == user_skill.skill_id
        )]
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
async def test_import_from_github_creates_personal_skill(
    fake_file_storage,
    monkeypatch,
):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "demo-skill-main/SKILL.md",
            "---\n"
            "name: demo-skill\n"
            "description: Demo skill\n"
            "---\n\n"
            "Run the demo.\n",
        )
    monkeypatch.setattr(
        "app.application.services.skill_service.fetch_github_skill_zipball",
        AsyncMock(return_value=buffer.getvalue()),
    )
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)

    skill = await service.import_from_github("user-1", "https://github.com/acme/demo-skill")

    assert skill.name == "demo-skill"
    assert skill.owner_type == SkillOwnerType.PERSONAL
    assert skill.source == SkillSource.GITHUB
    assert await user_skill_repo.count_by_user_id("user-1") == 1


@pytest.mark.asyncio
async def test_ensure_defaults_seeds_official_and_personal_skills(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)

    catalog, added = await service.get_state("user-2")

    assert len(added) == 6
    names = {skill.name for skill, _ in added}
    assert names >= {
        "skill-creator",
        "web-research",
        "summarize",
        "slides",
        "market-research",
        "data-viz",
    }
    assert len(catalog) >= len(added)
