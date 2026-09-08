import hashlib
import io
import zipfile
from datetime import datetime

import pytest

from app.application.errors.exceptions import BadRequestError
from app.application.services.skill_service import SkillService
from app.domain.models.file import FileInfo
from app.domain.models.skill import SkillSource
from app.domain.skills.archive import MAX_SKILL_PACKAGE_BYTES


class _FakeSkillRepository:
    def __init__(self):
        self.skills = []

    async def save_personal_skill(self, skill):
        self.skills.append(skill)


class _FakeUserSkillRepository:
    def __init__(self):
        self.items = []

    async def save(self, user_skill):
        self.items.append(user_skill)

    async def find_by_user_id_and_skill_id(self, user_id, skill_id):
        for item in self.items:
            if item.user_id == user_id and item.skill_id == skill_id:
                return item
        return None


class _FakeFileStorage:
    def __init__(self):
        self.files = {}

    async def upload_file(
        self,
        file_data,
        filename,
        user_id,
        content_type=None,
        metadata=None,
    ):
        data = file_data.read()
        file_id = f"file_{len(self.files) + 1}"
        self.files[file_id] = data
        return FileInfo(
            file_id=file_id,
            filename=filename,
            size=len(data),
            upload_date=datetime.utcnow(),
        )

    async def download_file(self, file_id, user_id=None):
        data = self.files[file_id]
        return io.BytesIO(data), FileInfo(
            file_id=file_id,
            filename="x.zip",
            size=len(data),
            upload_date=datetime.utcnow(),
        )


def _zip_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_ingest_stores_full_package():
    package_bytes = _zip_bytes(
        {
            "SKILL.md": (
                "---\n"
                "name: package-demo\n"
                "description: Package demo\n"
                "---\n\n"
                "Run the included script.\n"
            ),
            "scripts/a.py": "print('hello')\n",
        }
    )
    skill_repository = _FakeSkillRepository()
    user_skill_repository = _FakeUserSkillRepository()
    storage = _FakeFileStorage()
    service = SkillService(
        skill_repository,
        user_skill_repository,
        file_storage=storage,
    )

    skill = await service.ingest_skill_package(
        "user-1",
        package_bytes,
        source=SkillSource.UPLOAD,
        source_url="x.zip",
    )

    assert skill.name == "package-demo"
    assert skill.description == "Package demo"
    assert skill.body == "Run the included script."
    assert skill.package_file_id == "file_1"
    assert skill.package_sha256 == hashlib.sha256(package_bytes).hexdigest()
    assert skill_repository.skills == [skill]
    subscription = await user_skill_repository.find_by_user_id_and_skill_id(
        "user-1", skill.id
    )
    assert subscription.enabled is True

    downloaded, _ = await storage.download_file(skill.package_file_id)
    with zipfile.ZipFile(downloaded) as archive:
        assert "scripts/a.py" in archive.namelist()


@pytest.mark.asyncio
async def test_ingest_rejects_invalid_zip_as_bad_request():
    service = SkillService(
        _FakeSkillRepository(),
        _FakeUserSkillRepository(),
        file_storage=_FakeFileStorage(),
    )

    with pytest.raises(BadRequestError):
        await service.ingest_skill_package(
            "user-1",
            b"not a zip",
            source=SkillSource.UPLOAD,
            source_url="broken.zip",
        )


@pytest.mark.asyncio
async def test_ingest_rejects_aggregate_uncompressed_package_over_cap():
    package_bytes = _zip_bytes(
        {
            "SKILL.md": (
                "---\n"
                "name: oversized\n"
                "description: Oversized package\n"
                "---\n\n"
                "Tiny instructions.\n"
            ),
            "assets/oversized.txt": "x" * (MAX_SKILL_PACKAGE_BYTES + 1),
        }
    )
    assert len(package_bytes) < MAX_SKILL_PACKAGE_BYTES
    service = SkillService(
        _FakeSkillRepository(),
        _FakeUserSkillRepository(),
        file_storage=_FakeFileStorage(),
    )

    with pytest.raises(BadRequestError, match="uncompressed"):
        await service.ingest_skill_package(
            "user-1",
            package_bytes,
            source=SkillSource.UPLOAD,
            source_url="oversized.zip",
        )
