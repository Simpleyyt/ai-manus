from typing import List, Optional

from app.domain.models.skill import UserSkill
from app.domain.repositories.skill_repository import UserSkillRepository
from app.infrastructure.models.documents import UserSkillDocument


class MongoUserSkillRepository(UserSkillRepository):
    async def save(self, user_skill: UserSkill) -> None:
        mongo = await UserSkillDocument.find_one(
            UserSkillDocument.user_id == user_skill.user_id,
            UserSkillDocument.skill_id == user_skill.skill_id,
        )
        if not mongo:
            mongo = UserSkillDocument.from_domain(user_skill)
            await mongo.save()
            return
        user_skill.id = mongo.user_skill_id
        mongo.update_from_domain(user_skill)
        await mongo.save()

    async def find_by_user_id(self, user_id: str) -> List[UserSkill]:
        mongo_items = await UserSkillDocument.find(
            UserSkillDocument.user_id == user_id
        ).sort([("created_at", 1)]).to_list()
        return [item.to_domain() for item in mongo_items]

    async def find_by_user_id_and_skill_id(
        self, user_id: str, skill_id: str
    ) -> Optional[UserSkill]:
        mongo = await UserSkillDocument.find_one(
            UserSkillDocument.user_id == user_id,
            UserSkillDocument.skill_id == skill_id,
        )
        return mongo.to_domain() if mongo else None

    async def count_by_user_id(self, user_id: str) -> int:
        return await UserSkillDocument.find(
            UserSkillDocument.user_id == user_id
        ).count()
