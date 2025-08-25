from app.infrastructure.external.cache.redis_cache import RedisCache
from functools import lru_cache

@lru_cache()
def get_cache():
    """Get cache implementation"""
    return RedisCache()

__all__ = ['get_cache', 'RedisCache']
