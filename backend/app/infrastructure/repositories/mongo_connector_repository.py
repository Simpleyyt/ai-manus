from typing import List, Optional

from app.domain.models.connector import UserConnector
from app.domain.repositories.connector_repository import ConnectorRepository
from app.infrastructure.models.documents import UserConnectorDocument


class MongoConnectorRepository(ConnectorRepository):
    async def save(self, connector: UserConnector) -> None:
        mongo = await UserConnectorDocument.find_one(
            UserConnectorDocument.connector_id == connector.id,
            UserConnectorDocument.user_id == connector.user_id,
        )
        if not mongo:
            mongo = UserConnectorDocument.from_domain(connector)
            await mongo.save()
            return
        connector.id = mongo.connector_id
        mongo.update_from_domain(connector)
        await mongo.save()

    async def find_by_user_id(self, user_id: str) -> List[UserConnector]:
        mongo_items = await UserConnectorDocument.find(
            UserConnectorDocument.user_id == user_id
        ).sort([("created_at", 1)]).to_list()
        return [item.to_domain() for item in mongo_items]

    async def find_by_id_and_user_id(self, connector_id: str, user_id: str) -> Optional[UserConnector]:
        mongo = await UserConnectorDocument.find_one(
            UserConnectorDocument.connector_id == connector_id,
            UserConnectorDocument.user_id == user_id,
        )
        return mongo.to_domain() if mongo else None

    async def find_enabled_by_user_id(self, user_id: str) -> List[UserConnector]:
        mongo_items = await UserConnectorDocument.find(
            UserConnectorDocument.user_id == user_id,
            UserConnectorDocument.enabled == True,
        ).sort([("created_at", 1)]).to_list()
        return [item.to_domain() for item in mongo_items]

    async def delete_by_id_and_user_id(self, connector_id: str, user_id: str) -> bool:
        mongo = await UserConnectorDocument.find_one(
            UserConnectorDocument.connector_id == connector_id,
            UserConnectorDocument.user_id == user_id,
        )
        if not mongo:
            return False
        await mongo.delete()
        return True
