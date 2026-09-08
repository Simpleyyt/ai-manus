from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.skill import Skill, UserSkill


class SkillRepository(ABC):
    @abstractmethod
    async def save_personal_skill(self, skill: Skill) -> None:
        ...

    @abstractmethod
    async def find_personal_skills_by_user_id(self, user_id: str) -> List[Skill]:
        ...

    @abstractmethod
    async def find_personal_skill_by_id_and_user_id(
        self, skill_id: str, user_id: str
    ) -> Optional[Skill]:
        ...


class UserSkillRepository(ABC):
    @abstractmethod
    async def save(self, user_skill: UserSkill) -> None:
        ...

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[UserSkill]:
        ...

    @abstractmethod
    async def find_by_user_id_and_skill_id(
        self, user_id: str, skill_id: str
    ) -> Optional[UserSkill]:
        ...

    @abstractmethod
    async def count_by_user_id(self, user_id: str) -> int:
        ...
