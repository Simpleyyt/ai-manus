from typing import List, Optional

from app.domain.models.skill import Skill
from app.domain.repositories.skill_repository import SkillRepository
from app.infrastructure.models.documents import SkillDocument
import logging

logger = logging.getLogger(__name__)


class MongoSkillRepository(SkillRepository):
    async def save_personal_skill(self, skill: Skill) -> None:
        mongo_skill = await SkillDocument.find_one(SkillDocument.skill_id == skill.id)
        if not mongo_skill:
            mongo_skill = SkillDocument.from_domain(skill)
            await mongo_skill.save()
            return
        mongo_skill.update_from_domain(skill)
        await mongo_skill.save()

    async def find_personal_skills_by_user_id(self, user_id: str) -> List[Skill]:
        mongo_skills = await SkillDocument.find(
            SkillDocument.owner_user_id == user_id
        ).sort([("updated_at", -1)]).to_list()
        return [skill.to_domain() for skill in mongo_skills]

    async def find_personal_skill_by_id_and_user_id(
        self, skill_id: str, user_id: str
    ) -> Optional[Skill]:
        mongo_skill = await SkillDocument.find_one(
            SkillDocument.skill_id == skill_id,
            SkillDocument.owner_user_id == user_id,
        )
        return mongo_skill.to_domain() if mongo_skill else None
