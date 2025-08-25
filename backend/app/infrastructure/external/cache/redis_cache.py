import json
import logging
from typing import Optional, Any
from app.domain.external.cache import Cache
from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis implementation of Cache interface"""
    
    def __init__(self):
        self.redis_client = get_redis()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL"""
        try:
            await self.redis_client.initialize()
            
            # Serialize value to JSON
            serialized_value = json.dumps(value)
            
            if ttl is not None:
                # Set with TTL
                result = await self.redis_client.client.setex(key, ttl, serialized_value)
            else:
                # Set without TTL
                result = await self.redis_client.client.set(key, serialized_value)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache"""
        try:
            await self.redis_client.initialize()
            
            value = await self.redis_client.client.get(key)
            if value is None:
                return None
            
            # Deserialize from JSON
            return json.loads(value)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to deserialize cache value for key {key}")
            # Delete corrupted data
            await self.delete(key)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        try:
            await self.redis_client.initialize()
            
            result = await self.redis_client.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            await self.redis_client.initialize()
            
            result = await self.redis_client.client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check existence of cache key {key}: {str(e)}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get the remaining TTL of a key"""
        try:
            await self.redis_client.initialize()
            
            ttl = await self.redis_client.client.ttl(key)
            
            # Redis returns -1 if key exists but has no expiration
            # Redis returns -2 if key doesn't exist
            if ttl == -2:
                return None  # Key doesn't exist
            elif ttl == -1:
                return None  # Key exists but has no expiration
            else:
                return ttl  # TTL in seconds
                
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {str(e)}")
            return None
    
    async def keys(self, pattern: str) -> list[str]:
        """Get all keys matching a pattern"""
        try:
            await self.redis_client.initialize()
            
            keys = await self.redis_client.client.keys(pattern)
            return keys if keys else []
            
        except Exception as e:
            logger.error(f"Failed to get keys with pattern {pattern}: {str(e)}")
            return []
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            await self.redis_client.initialize()
            
            keys = await self.keys(pattern)
            if not keys:
                return 0
            
            result = await self.redis_client.client.delete(*keys)
            return result
            
        except Exception as e:
            logger.error(f"Failed to clear keys with pattern {pattern}: {str(e)}")
            return 0
