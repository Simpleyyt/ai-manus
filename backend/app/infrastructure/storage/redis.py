from redis.asyncio import Redis
from functools import lru_cache
import logging
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._client: Redis | None = None
        self._settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._client is not None:
            return
            
        try:
            # Connect to Redis
            self._client = Redis.from_url(
                self._settings.redis_url,
                decode_responses=True
            )
            # Verify the connection
            await self._client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")
        get_redis.cache_clear()
    
    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client

@lru_cache
def get_redis() -> RedisClient:
    """Get the Redis client instance."""
    return RedisClient() 