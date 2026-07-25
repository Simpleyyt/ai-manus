from typing import Set
from datetime import datetime, timezone
from app.domain.repositories.file_favorite_repository import FileFavoriteRepository
from app.infrastructure.models.documents import FileFavoriteDocument
import logging

logger = logging.getLogger(__name__)


class MongoFileFavoriteRepository(FileFavoriteRepository):
    """MongoDB implementation of FileFavoriteRepository"""

    async def set_favorite(self, user_id: str, file_id: str, is_favorite: bool) -> None:
        existing = await FileFavoriteDocument.find_one(
            FileFavoriteDocument.user_id == user_id,
            FileFavoriteDocument.file_id == file_id,
        )
        if is_favorite:
            if existing:
                return
            await FileFavoriteDocument(
                user_id=user_id,
                file_id=file_id,
                created_at=datetime.now(timezone.utc),
            ).insert()
            logger.info("File %s favorited by user %s", file_id, user_id)
            return
        if existing:
            await existing.delete()
            logger.info("File %s unfavorited by user %s", file_id, user_id)

    async def list_favorite_file_ids(self, user_id: str) -> Set[str]:
        docs = await FileFavoriteDocument.find(
            FileFavoriteDocument.user_id == user_id
        ).to_list()
        return {doc.file_id for doc in docs}
