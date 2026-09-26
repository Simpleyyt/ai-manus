from typing import List, Optional, Protocol

from app.domain.models.connector_catalog import CatalogConnector


class ConnectorCatalogRepository(Protocol):
    def list_entries(self) -> List[CatalogConnector]:
        ...

    def get(self, uid: str) -> Optional[CatalogConnector]:
        ...
