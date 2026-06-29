"""Shared infrastructure bootstrap helpers.

Both the FastAPI application (``app.main``) and the Celery worker
(``app.infrastructure.external.task.celery_app``) need to initialize the same
backing services — MongoDB + Beanie and Redis — before they can do any work.
Centralizing the logic here keeps the two entry points in sync.
"""

import logging

from beanie import init_beanie

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.infrastructure.models.documents import (
    AgentDocument,
    SessionDocument,
    UserDocument,
    ClawDocument,
)

logger = logging.getLogger(__name__)

DOCUMENT_MODELS = [AgentDocument, SessionDocument, UserDocument, ClawDocument]


async def init_storage() -> None:
    """Initialize MongoDB + Beanie and Redis connections."""
    settings = get_settings()

    await get_mongodb().initialize()
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=DOCUMENT_MODELS,
    )
    logger.info("Successfully initialized Beanie")

    await get_redis().initialize()
    logger.info("Successfully initialized Redis")


async def shutdown_storage() -> None:
    """Shutdown MongoDB and Redis connections."""
    await get_mongodb().shutdown()
    await get_redis().shutdown()
    logger.info("Storage connections closed")
