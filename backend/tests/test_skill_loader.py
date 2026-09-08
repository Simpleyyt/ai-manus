import io
import zipfile

import pytest

from app.application.services.skill_service import SkillService
from app.domain.models.skill import SkillOwnerType, SkillSource
from app.domain.skills.body import resolve_skill_body
from app.domain.skills.skill_md import (
    extract_skill_md_from_bytes,
    parse_skill_md,
)
from app.application.data.official_skills import OFFICIAL_SKILL_BY_ID


SAMPLE_SKILL_MD = """---
name: demo-skill
description: Demo skill for tests
---

# Demo Skill

Follow these steps carefully.
"""


def test_parse_skill_md_reads_frontmatter_and_body():
    parsed = parse_skill_md(SAMPLE_SKILL_MD)

    assert parsed.name == "demo-skill"
    assert parsed.description == "Demo skill for tests"
    assert "Follow these steps carefully." in parsed.body


def test_extract_skill_md_from_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("SKILL.md", SAMPLE_SKILL_MD)
    data = buffer.getvalue()

    content = extract_skill_md_from_bytes(data, "demo-skill.zip")
    assert "demo-skill" in content


def test_resolve_skill_body_prefers_official_catalog_body():
    skill = OFFICIAL_SKILL_BY_ID["skill_market_research"]
    body = resolve_skill_body(skill)

    assert "structured brief" in body
    assert "Research markets" in body


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
async def test_import_from_upload_parses_skill_md(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)

    skill = await service.import_from_upload(
        "user-1",
        "demo-skill.md",
        SAMPLE_SKILL_MD.encode("utf-8"),
    )

    assert skill.name == "demo-skill"
    assert skill.description == "Demo skill for tests"
    assert skill.body == "# Demo Skill\n\nFollow these steps carefully."
    assert skill.source == SkillSource.UPLOAD
    assert skill.owner_type == SkillOwnerType.PERSONAL
