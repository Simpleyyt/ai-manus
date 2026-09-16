from typing import List, Optional, Protocol

from app.domain.models.connector import UserConnector


class ConnectorRepository(Protocol):
    async def save(self, connector: UserConnector) -> None:
        ...

    async def find_by_user_id(self, user_id: str) -> List[UserConnector]:
        ...

    async def find_by_id_and_user_id(self, connector_id: str, user_id: str) -> Optional[UserConnector]:
        ...

    async def find_enabled_by_user_id(self, user_id: str) -> List[UserConnector]:
        ...

    async def delete_by_id_and_user_id(self, connector_id: str, user_id: str) -> bool:
        ...
