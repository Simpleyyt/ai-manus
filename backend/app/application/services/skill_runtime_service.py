import logging
import re
import shlex

from app.application.data.official_skill_packages import official_package_dir
from app.application.services.skill_service import SkillService
from app.domain.models.message import Message, RequiredSkill, SkillContext
from app.domain.models.skill import Skill, SkillOwnerType
from app.domain.services.skills.invocation import parse_skill_invocation
from app.domain.services.prompts.system import (
    format_skill_catalog,
    format_skill_context,
)
from app.domain.skills.archive import iter_package_files
from app.domain.skills.body import resolve_skill_body
from app.domain.skills.package import SKILLS_ROOT, build_skill_md_file, skill_dir

logger = logging.getLogger(__name__)

_SKILL_SYNC_SESSION_ID = "skill-sync"
_SKILL_SYNC_EXEC_DIR = "/home/ubuntu"


class SkillRuntimeService:
    """Resolve skill invocations and build L1/L2 prompt sections for agents."""

    def __init__(self, skill_service: SkillService):
        self._skill_service = skill_service

    async def list_enabled_skill_pairs(self, user_id: str) -> list[tuple[str, str]]:
        """Enabled skill (name, description) pairs for L1 catalog / load_skill."""
        skills = await self._skill_service.list_enabled_skills(user_id)
        return [(skill.name, skill.description or "") for skill in skills]

    async def build_enabled_skill_bodies(self, user_id: str) -> dict[str, str]:
        """SKILL.md bodies for enabled skills (used by ``load_skill``)."""
        skills = await self._skill_service.list_enabled_skills(user_id)
        bodies: dict[str, str] = {}
        for skill in skills:
            body = resolve_skill_body(skill)
            if (body or "").strip():
                bodies[skill.name] = body
        return bodies

    async def build_skill_catalog_section(self, user_id: str) -> str:
        """L1: enabled skill metadata for the system prompt at session start."""
        pairs = await self.list_enabled_skill_pairs(user_id)
        return format_skill_catalog(pairs)

    async def sync_enabled_skills_to_sandbox(self, user_id: str, sandbox) -> int:
        """L3: write enabled skill packages under /home/ubuntu/skills/{name}/.

        Returns the number of skills written.
        """
        skills = await self._skill_service.list_enabled_skills(user_id)
        enabled_names = {skill.name for skill in skills}
        written = 0
        for skill in skills:
            try:
                files = await self._package_files(skill)
                await self._delete_tree(sandbox, skill_dir(skill.name))
                if await self._write_package_files(sandbox, skill.name, files):
                    written += 1
            except Exception:
                logger.exception(
                    "Failed to sync skill /%s to sandbox",
                    skill.name,
                )
        await self._remove_disabled_skill_dirs(sandbox, enabled_names)
        if written:
            logger.info(
                "Synced %s skill package(s) to sandbox for user %s",
                written,
                user_id,
            )
        return written

    @staticmethod
    async def _delete_tree(sandbox, path: str) -> None:
        await SkillRuntimeService._exec_skill_command(
            sandbox,
            f"rm -rf {shlex.quote(path)}",
        )

    @classmethod
    async def _remove_disabled_skill_dirs(
        cls,
        sandbox,
        enabled_names: set[str],
    ) -> None:
        try:
            root = shlex.quote(SKILLS_ROOT)
            output = await cls._exec_skill_command(
                sandbox,
                (
                    f"if [ -d {root} ]; then "
                    f"find {root} -mindepth 1 -maxdepth 1 -type d "
                    "-exec basename '{}' ';'; "
                    "fi"
                ),
            )
            for name in output.splitlines():
                if name and name not in enabled_names:
                    await cls._delete_tree(
                        sandbox,
                        f"{SKILLS_ROOT}/{name}",
                    )
        except Exception:
            logger.exception("Failed to remove disabled skill directories from sandbox")

    @staticmethod
    async def _exec_skill_command(sandbox, command: str) -> str:
        result = await sandbox.exec_command(
            _SKILL_SYNC_SESSION_ID,
            _SKILL_SYNC_EXEC_DIR,
            command,
        )
        if not result or getattr(result, "success", True) is False:
            raise RuntimeError(f"Sandbox command failed: {command}")

        data = getattr(result, "data", None)
        if isinstance(data, dict):
            returncode = data.get("returncode")
            output = data.get("output", "")
        else:
            returncode = getattr(data, "returncode", None)
            output = getattr(data, "output", "")
        if returncode not in (None, 0):
            raise RuntimeError(
                f"Sandbox command exited with status {returncode}: {command}"
            )
        return output if isinstance(output, str) else ""

    async def _package_files(self, skill: Skill) -> list[tuple[str, bytes]]:
        if skill.owner_type == SkillOwnerType.OFFICIAL:
            package_dir = official_package_dir(skill.name)
            if package_dir is not None:
                return [
                    (path.relative_to(package_dir).as_posix(), path.read_bytes())
                    for path in sorted(package_dir.rglob("*"))
                    if path.is_file()
                ]

        package_bytes = await self._skill_service.get_package_bytes(skill)
        if package_bytes is not None:
            return iter_package_files(package_bytes)

        return [("SKILL.md", build_skill_md_file(skill).encode("utf-8"))]

    @staticmethod
    async def _write_package_files(
        sandbox,
        skill_name: str,
        files: list[tuple[str, bytes]],
    ) -> bool:
        success = True
        for relpath, data in files:
            path = f"{skill_dir(skill_name)}/{relpath}"
            try:
                content = data.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning(
                    "Skipping non-UTF-8 skill file /%s at sandbox path %s",
                    skill_name,
                    path,
                )
                continue
            result = await sandbox.file_write(path, content)
            if result and getattr(result, "success", True) is False:
                logger.warning(
                    "Failed to sync skill /%s to sandbox path %s: %s",
                    skill_name,
                    path,
                    getattr(result, "message", result),
                )
                success = False
        return success

    async def resolve_message(self, user_id: str, message: Message) -> Message:
        """Resolve structured requiredSkills or /{name} text into L2 active skill context."""
        parsed = parse_skill_invocation(message.message) if not message.required_skills else None
        resolved_skills = await self._resolve_active_skills(user_id, message)
        if not resolved_skills:
            return message

        if parsed and parsed.task:
            task = parsed.task
        else:
            task = self._normalize_task_text(message.message, resolved_skills)
        skill_contexts = [
            SkillContext(
                skill_id=skill.id,
                name=skill.name,
                body=resolve_skill_body(skill),
            )
            for skill in resolved_skills
        ]
        primary = skill_contexts[0]

        return Message(
            message=task,
            attachments=message.attachments,
            required_skills=message.required_skills,
            skill=primary,
        )

    async def _resolve_active_skills(
        self, user_id: str, message: Message
    ) -> list[Skill]:
        if message.required_skills:
            skills: list[Skill] = []
            for req in message.required_skills:
                skill = await self._skill_service.resolve_enabled_skill_by_id(
                    user_id, req.skill_id
                )
                if not skill:
                    skill = await self._skill_service.resolve_enabled_skill_by_name(
                        user_id, req.name
                    )
                if skill:
                    skills.append(skill)
                else:
                    logger.info(
                        "Ignoring required skill %s for user %s (not added or disabled)",
                        req.skill_id or req.name,
                        user_id,
                    )
            if skills:
                return skills

        parsed = parse_skill_invocation(message.message)
        if not parsed:
            return []

        skill = await self._skill_service.resolve_enabled_skill_by_name(
            user_id, parsed.name
        )
        if not skill:
            logger.info(
                "Ignoring skill invocation /%s for user %s (not added or disabled)",
                parsed.name,
                user_id,
            )
            return []
        return [skill]

    @staticmethod
    def _normalize_task_text(text: str, skills: list[Skill]) -> str:
        task = (text or "").strip()
        for skill in skills:
            task = SkillRuntimeService._strip_skill_prefix(task, skill.name)
        if not task:
            primary = skills[0]
            return f"Follow the /{primary.name} skill."
        return task

    @staticmethod
    def _strip_skill_prefix(text: str, skill_name: str) -> str:
        if not text or not skill_name:
            return (text or "").strip()
        pattern = re.compile(
            rf"^/{re.escape(skill_name)}\s*",
            re.IGNORECASE,
        )
        stripped = pattern.sub("", text.strip(), count=1).strip()
        if stripped != text.strip():
            return stripped
        # Chip may serialize as name without leading slash
        pattern2 = re.compile(
            rf"^{re.escape(skill_name)}\s*",
            re.IGNORECASE,
        )
        return pattern2.sub("", text.strip(), count=1).strip()

    def format_agent_skill_context(self, message: Message) -> str:
        """Soft L2: activation marker pointing at SKILL.md (no body inject)."""
        if not message.skill:
            return ""
        return format_skill_context(
            name=message.skill.name,
            task=message.message,
        )

    @staticmethod
    def format_chat_system_skill(message: Message) -> str:
        """Chat mode has no file tools — activation note only, no body inject."""
        if not message.skill:
            return ""
        name = message.skill.name
        sections = [
            "<active_skill>",
            f"The user invoked skill `/{name}` for this turn.",
            "Chat mode cannot read sandbox skill files; answer from general knowledge "
            "and the skill name/task only. Do not invent a detailed skill workflow.",
        ]
        user_task = (message.message or "").strip()
        if user_task:
            sections.extend(["", "User task for this turn:", user_task])
        sections.append("</active_skill>")
        return "\n".join(sections)
