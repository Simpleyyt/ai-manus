from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional
import logging
from app.core.config import get_settings
from functools import lru_cache

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self._client: Optional[AsyncMongoClient] = None
        self._settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize MongoDB connection and Beanie ODM."""
        if self._client is not None:
            return
            
        try:
            if self._settings.mongodb_username and self._settings.mongodb_password:
                self._client = AsyncMongoClient(
                    self._settings.mongodb_uri,
                    username=self._settings.mongodb_username,
                    password=self._settings.mongodb_password,
                )
            else:
                self._client = AsyncMongoClient(
                    self._settings.mongodb_uri,
                )
            await self._client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Beanie: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown MongoDB connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from MongoDB")
        get_mongodb.cache_clear()
    
    @property
    def client(self) -> AsyncMongoClient:
        """Return initialized MongoDB client"""
        if self._client is None:
            raise RuntimeError("MongoDB client not initialized. Call initialize() first.")
        return self._client


@lru_cache()
def get_mongodb() -> MongoDB:
    """Get the MongoDB instance."""
    return MongoDB()

