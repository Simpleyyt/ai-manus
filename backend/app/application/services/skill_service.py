import logging
import io
import re
import zipfile
from datetime import UTC, datetime
from typing import List, Optional
import uuid

from app.application.data.official_skills import (
    DEFAULT_ADDED_OFFICIAL_SKILL_IDS,
    DEFAULT_PERSONAL_SKILL,
    OFFICIAL_SKILL_BY_ID,
    OFFICIAL_SKILLS,
)
from app.application.errors.exceptions import BadRequestError, NotFoundError
from app.application.services.skill_github import (
    fetch_github_skill_zipball,
    parse_github_repo_url,
)
from app.domain.external.file import FileStorage
from app.domain.skills.archive import (
    SkillArchiveError,
    ensure_package_size,
    normalize_package_bytes,
    package_sha256,
    read_skill_md_from_package,
)
from app.domain.skills.body import resolve_skill_body
from app.domain.skills.skill_md import parse_skill_md
from app.domain.models.skill import Skill, SkillOwnerType, SkillSource, UserSkill
from app.domain.repositories.skill_repository import SkillRepository, UserSkillRepository

logger = logging.getLogger(__name__)

_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SkillService:
    def __init__(
        self,
        skill_repository: SkillRepository,
        user_skill_repository: UserSkillRepository,
        file_storage: FileStorage,
    ):
        self._skill_repository = skill_repository
        self._user_skill_repository = user_skill_repository
        self._file_storage = file_storage

    async def get_state(self, user_id: str) -> tuple[List[Skill], List[tuple[Skill, UserSkill]]]:
        await self._ensure_default_subscriptions(user_id)
        personal_skills = await self._skill_repository.find_personal_skills_by_user_id(user_id)
        catalog = [*OFFICIAL_SKILLS, *personal_skills]
        catalog_by_id = {skill.id: skill for skill in catalog}
        subscriptions = await self._user_skill_repository.find_by_user_id(user_id)
        added: List[tuple[Skill, UserSkill]] = []
        for subscription in subscriptions:
            skill = catalog_by_id.get(subscription.skill_id)
            if not skill:
                skill = await self._skill_repository.find_personal_skill_by_id_and_user_id(
                    subscription.skill_id, user_id
                )
            if skill:
                added.append((skill, subscription))
        return catalog, added

    async def add_skills(self, user_id: str, skill_ids: List[str]) -> List[Skill]:
        await self._ensure_default_subscriptions(user_id)
        catalog, _ = await self.get_state(user_id)
        catalog_by_id = {skill.id: skill for skill in catalog}
        added: List[Skill] = []
        for skill_id in skill_ids:
            skill = catalog_by_id.get(skill_id)
            if not skill:
                raise NotFoundError(f"Skill not found: {skill_id}")
            existing = await self._user_skill_repository.find_by_user_id_and_skill_id(
                user_id, skill_id
            )
            if existing:
                if not existing.enabled:
                    existing.enabled = True
                    existing.updated_at = datetime.now(UTC)
                    await self._user_skill_repository.save(existing)
                continue
            subscription = UserSkill(user_id=user_id, skill_id=skill_id, enabled=True)
            await self._user_skill_repository.save(subscription)
            added.append(skill)
        return added

    async def set_skill_enabled(self, user_id: str, skill_id: str, enabled: bool) -> UserSkill:
        subscription = await self._user_skill_repository.find_by_user_id_and_skill_id(
            user_id, skill_id
        )
        if not subscription:
            raise NotFoundError("Skill subscription not found")
        subscription.enabled = enabled
        subscription.updated_at = datetime.now(UTC)
        await self._user_skill_repository.save(subscription)
        return subscription

    async def import_from_github(self, user_id: str, url: str) -> Skill:
        owner, repo = parse_github_repo_url(url)
        package_bytes = await fetch_github_skill_zipball(owner, repo)
        return await self.ingest_skill_package(
            user_id,
            package_bytes,
            source=SkillSource.GITHUB,
            source_url=url,
        )

    async def import_from_upload(
        self, user_id: str, filename: str, data: bytes
    ) -> Skill:
        try:
            package_bytes = normalize_package_bytes(data, filename)
        except (SkillArchiveError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
            raise BadRequestError(str(exc)) from exc
        return await self.ingest_skill_package(
            user_id,
            package_bytes,
            source=SkillSource.UPLOAD,
            source_url=filename,
        )

    async def ingest_skill_package(
        self,
        user_id: str,
        package_bytes: bytes,
        *,
        source: SkillSource,
        source_url: str,
    ) -> Skill:
        try:
            ensure_package_size(package_bytes)
            parsed = parse_skill_md(read_skill_md_from_package(package_bytes))
        except (SkillArchiveError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
            raise BadRequestError(str(exc)) from exc

        name = parsed.name or self._normalize_skill_name(
            re.sub(r"\.(zip|skill|md)$", "", source_url.strip(), flags=re.IGNORECASE)
        )
        if not name:
            raise BadRequestError("Invalid skill name in SKILL.md")

        description = parsed.description or f"Uploaded from {source_url}"
        body = parsed.body or description
        uploaded = await self._file_storage.upload_file(
            io.BytesIO(package_bytes),
            filename=f"{name}.zip",
            user_id=user_id,
            content_type="application/zip",
            metadata={"kind": "skill_package"},
        )
        skill = Skill(
            id=f"skill_{source.value}_{uuid.uuid4().hex[:12]}",
            name=name,
            description=description,
            body=body,
            owner_type=SkillOwnerType.PERSONAL,
            owner_user_id=user_id,
            source=source,
            source_url=source_url,
            package_file_id=uploaded.file_id,
            package_sha256=package_sha256(package_bytes),
        )
        await self._skill_repository.save_personal_skill(skill)
        await self._add_subscription(user_id, skill.id, enabled=True)
        return skill

    async def get_package_bytes(self, skill: Skill) -> Optional[bytes]:
        """Download a stored personal skill package."""
        if not skill.package_file_id:
            return None
        stream, _ = await self._file_storage.download_file(
            skill.package_file_id,
            skill.owner_user_id,
        )
        return stream.read()

    async def _ensure_default_subscriptions(self, user_id: str) -> None:
        count = await self._user_skill_repository.count_by_user_id(user_id)
        if count > 0:
            return
        for skill_id in DEFAULT_ADDED_OFFICIAL_SKILL_IDS:
            await self._add_subscription(user_id, skill_id, enabled=True)
        personal = Skill(
            id=f"skill_personal_{uuid.uuid4().hex[:12]}",
            name=DEFAULT_PERSONAL_SKILL["name"],
            description=DEFAULT_PERSONAL_SKILL["description"],
            body=DEFAULT_PERSONAL_SKILL.get("body"),
            owner_type=SkillOwnerType.PERSONAL,
            owner_user_id=user_id,
            source=SkillSource.CATALOG,
        )
        await self._skill_repository.save_personal_skill(personal)
        await self._add_subscription(user_id, personal.id, enabled=True)
        logger.info("Seeded default skills for user %s", user_id)

    async def _add_subscription(
        self, user_id: str, skill_id: str, *, enabled: bool
    ) -> UserSkill:
        existing = await self._user_skill_repository.find_by_user_id_and_skill_id(
            user_id, skill_id
        )
        if existing:
            if existing.enabled != enabled:
                existing.enabled = enabled
                existing.updated_at = datetime.now(UTC)
                await self._user_skill_repository.save(existing)
            return existing
        subscription = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            enabled=enabled,
        )
        await self._user_skill_repository.save(subscription)
        return subscription

    @staticmethod
    def _normalize_skill_name(raw: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
        if not normalized or not _SKILL_NAME_PATTERN.fullmatch(normalized):
            return ""
        return normalized

    @staticmethod
    def resolve_official_skill(skill_id: str) -> Optional[Skill]:
        return OFFICIAL_SKILL_BY_ID.get(skill_id)

    async def resolve_enabled_skill_by_name(
        self, user_id: str, skill_name: str
    ) -> Optional[Skill]:
        normalized = skill_name.strip().lower().lstrip("/")
        if not normalized:
            return None
        catalog, added = await self.get_state(user_id)
        catalog_by_name = {skill.name.lower(): skill for skill in catalog}
        skill = catalog_by_name.get(normalized)
        if not skill:
            return None
        subscription = await self._user_skill_repository.find_by_user_id_and_skill_id(
            user_id, skill.id
        )
        if not subscription or not subscription.enabled:
            return None
        return skill

    async def resolve_enabled_skill_by_id(
        self, user_id: str, skill_id: str
    ) -> Optional[Skill]:
        if not skill_id.strip():
            return None
        catalog, added = await self.get_state(user_id)
        catalog_by_id = {skill.id: skill for skill in catalog}
        skill = catalog_by_id.get(skill_id)
        if not skill:
            skill = await self._skill_repository.find_personal_skill_by_id_and_user_id(
                skill_id, user_id
            )
        if not skill:
            return None
        subscription = await self._user_skill_repository.find_by_user_id_and_skill_id(
            user_id, skill.id
        )
        if not subscription or not subscription.enabled:
            return None
        return skill

    async def list_enabled_skills(self, user_id: str) -> List[Skill]:
        """Return skills the user has added and enabled (L1 catalog source)."""
        _, added = await self.get_state(user_id)
        return [skill for skill, subscription in added if subscription.enabled]
