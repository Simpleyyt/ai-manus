from typing import List, Optional, Protocol

from app.domain.models.connector import Connector


class ConnectorRepository(Protocol):
    async def save(self, connector: Connector) -> None:
        ...

    async def delete(self, connector_id: str, user_id: str) -> bool:
        ...

    async def find_by_user_id(self, user_id: str) -> List[Connector]:
        ...

    async def find_by_id_and_user_id(
        self, connector_id: str, user_id: str
    ) -> Optional[Connector]:
        ...

    async def find_by_user_id_and_name(
        self, user_id: str, name: str
    ) -> Optional[Connector]:
        ...
