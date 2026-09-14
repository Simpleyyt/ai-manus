import io
import zipfile
from types import SimpleNamespace

import pytest

from app.application.services.skill_runtime_service import SkillRuntimeService
from app.application.services.skill_service import SkillService
from app.domain.models.skill import Skill, SkillOwnerType, SkillSource
from app.domain.skills.package import (
    SKILLS_ROOT,
    build_skill_md_file,
    skill_dir,
    skill_md_path,
)
from app.domain.services.prompts.system import format_skill_catalog, format_skill_context


def test_skill_paths():
    assert skill_dir("excel-generator") == f"{SKILLS_ROOT}/excel-generator"
    assert skill_md_path("excel-generator") == f"{SKILLS_ROOT}/excel-generator/SKILL.md"


def test_build_skill_md_file_includes_frontmatter_and_body():
    skill = Skill(
        id="skill_demo",
        name="demo-skill",
        description="A demo",
        body="# Demo\n\nDo the thing.",
        owner_type=SkillOwnerType.PERSONAL,
        source=SkillSource.UPLOAD,
    )
    content = build_skill_md_file(skill)
    assert content.startswith("---\n")
    assert "name: demo-skill" in content
    assert "description: A demo" in content
    assert "# Demo" in content
    assert "Do the thing." in content


def test_format_skill_catalog_mentions_sandbox_path():
    catalog = format_skill_catalog([("slides", "Make slides")])
    assert "/home/ubuntu/skills/slides/SKILL.md" in catalog
    assert "/slides" in catalog
    assert "load_skill" in catalog


def test_format_skill_context_requires_load_skill():
    section = format_skill_context(name="slides", body="Make nice slides.", task="deck")
    assert "MUST call `load_skill`" in section
    assert "slides" in section
    assert "<skill_instructions>" not in section
    assert "Make nice slides." not in section
    assert "deck" in section


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


class _FakeSandbox:
    def __init__(self, skill_directories=None):
        self.writes: list[tuple[str, str]] = []
        self.skill_directories = skill_directories or []
        self.exec_calls: list[tuple[str, str, str]] = []
        self.operations: list[tuple[str, str]] = []

    async def file_write(self, file: str, content: str, **kwargs):
        self.writes.append((file, content))
        self.operations.append(("write", file))
        return SimpleNamespace(success=True)

    async def exec_command(self, session_id: str, exec_dir: str, command: str):
        self.exec_calls.append((session_id, exec_dir, command))
        self.operations.append(("exec", command))
        return SimpleNamespace(
            success=True,
            data={"output": "\n".join(self.skill_directories)},
        )


def _zip_bytes(files: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_sync_writes_skill_md_and_script(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)
    sandbox = _FakeSandbox()
    package_bytes = _zip_bytes(
        {
            "SKILL.md": (
                "---\n"
                "name: demo\n"
                "description: Package demo\n"
                "---\n\n"
                "Run the included script.\n"
            ),
            "scripts/hello.py": "print('hello')\n",
        }
    )
    await service.ingest_skill_package(
        "user-1",
        package_bytes,
        source=SkillSource.UPLOAD,
        source_url="demo.zip",
    )

    count = await runtime.sync_enabled_skills_to_sandbox("user-1", sandbox)

    assert count == 1
    writes = dict(sandbox.writes)
    assert writes[f"{SKILLS_ROOT}/demo/SKILL.md"].startswith("---\nname: demo\n")
    assert writes[f"{SKILLS_ROOT}/demo/scripts/hello.py"] == "print('hello')\n"


@pytest.mark.asyncio
async def test_sync_skips_binary_file_and_writes_remaining_utf8_files(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)
    sandbox = _FakeSandbox()
    package_bytes = _zip_bytes(
        {
            "SKILL.md": (
                "---\n"
                "name: binary-demo\n"
                "description: Binary package demo\n"
                "---\n\n"
                "Use the package.\n"
            ),
            "assets/x.bin": b"\xff\xfe",
        }
    )
    await service.ingest_skill_package(
        "user-1",
        package_bytes,
        source=SkillSource.UPLOAD,
        source_url="binary-demo.zip",
    )

    count = await runtime.sync_enabled_skills_to_sandbox("user-1", sandbox)

    assert count == 1
    writes = dict(sandbox.writes)
    assert f"{SKILLS_ROOT}/binary-demo/SKILL.md" in writes
    assert f"{SKILLS_ROOT}/binary-demo/assets/x.bin" not in writes


@pytest.mark.asyncio
async def test_sync_enabled_skills_to_sandbox_writes_skill_md(fake_file_storage):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)
    sandbox = _FakeSandbox()

    await service.add_skills("user-1", ["skill_market_research", "skill_slides"])
    count = await runtime.sync_enabled_skills_to_sandbox("user-1", sandbox)

    assert count >= 2
    paths = {path for path, _ in sandbox.writes}
    assert f"{SKILLS_ROOT}/market-research/SKILL.md" in paths
    assert f"{SKILLS_ROOT}/slides/SKILL.md" in paths
    market = next(c for p, c in sandbox.writes if p.endswith("market-research/SKILL.md"))
    assert "name: market-research" in market
    assert "structured brief" in market.lower() or "Market Research" in market


@pytest.mark.asyncio
async def test_sync_clears_enabled_skill_and_removes_stale_skill_directories(
    fake_file_storage,
):
    skill_repo = _FakeSkillRepository()
    user_skill_repo = _FakeUserSkillRepository()
    service = SkillService(skill_repo, user_skill_repo, fake_file_storage)
    runtime = SkillRuntimeService(service)
    await service.add_skills("user-1", ["skill_slides"])
    slides_dir = f"{SKILLS_ROOT}/slides"
    stale_dir = f"{SKILLS_ROOT}/disabled-skill"
    sandbox = _FakeSandbox(["slides", "disabled-skill"])

    await runtime.sync_enabled_skills_to_sandbox("user-1", sandbox)

    assert all(
        session_id == "skill-sync" and exec_dir == "/home/ubuntu"
        for session_id, exec_dir, _ in sandbox.exec_calls
    )
    commands = [command for _, _, command in sandbox.exec_calls]
    assert f"rm -rf {slides_dir}" in commands
    assert sandbox.operations.index(("exec", f"rm -rf {slides_dir}")) < next(
        index
        for index, (operation, path) in enumerate(sandbox.operations)
        if operation == "write" and path.startswith(f"{slides_dir}/")
    )
    assert any("find " in command for command in commands)
    assert f"rm -rf {stale_dir}" in commands
