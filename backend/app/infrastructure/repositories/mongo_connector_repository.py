from typing import List, Optional

from app.domain.models.connector import Connector
from app.domain.repositories.connector_repository import ConnectorRepository
from app.infrastructure.models.documents import ConnectorDocument


class MongoConnectorRepository(ConnectorRepository):
    async def save(self, connector: Connector) -> None:
        mongo = await ConnectorDocument.find_one(
            ConnectorDocument.connector_id == connector.id
        )
        if not mongo:
            mongo = ConnectorDocument.from_domain(connector)
            await mongo.save()
            return
        mongo.update_from_domain(connector)
        await mongo.save()

    async def delete(self, connector_id: str, user_id: str) -> bool:
        mongo = await ConnectorDocument.find_one(
            ConnectorDocument.connector_id == connector_id,
            ConnectorDocument.user_id == user_id,
        )
        if not mongo:
            return False
        await mongo.delete()
        return True

    async def find_by_user_id(self, user_id: str) -> List[Connector]:
        mongo_items = await ConnectorDocument.find(
            ConnectorDocument.user_id == user_id
        ).sort([("updated_at", -1)]).to_list()
        return [item.to_domain() for item in mongo_items]

    async def find_by_id_and_user_id(
        self, connector_id: str, user_id: str
    ) -> Optional[Connector]:
        mongo = await ConnectorDocument.find_one(
            ConnectorDocument.connector_id == connector_id,
            ConnectorDocument.user_id == user_id,
        )
        return mongo.to_domain() if mongo else None

    async def find_by_user_id_and_name(
        self, user_id: str, name: str
    ) -> Optional[Connector]:
        mongo = await ConnectorDocument.find_one(
            ConnectorDocument.user_id == user_id,
            ConnectorDocument.name == name,
        )
        return mongo.to_domain() if mongo else None

    async def find_by_user_id_and_catalog_uid(
        self, user_id: str, catalog_uid: str
    ) -> Optional[Connector]:
        if not catalog_uid:
            return None
        mongo = await ConnectorDocument.find_one(
            ConnectorDocument.user_id == user_id,
            ConnectorDocument.catalog_uid == catalog_uid,
        )
        return mongo.to_domain() if mongo else None
