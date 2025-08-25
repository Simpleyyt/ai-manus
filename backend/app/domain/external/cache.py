from typing import Protocol, Optional, Any
from datetime import timedelta

class Cache(Protocol):
    """Cache storage interface for temporary data storage"""
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL (time to live)
        
        Args:
            key: The cache key
            value: The value to store (will be JSON serialized)
            ttl: Time to live in seconds, None means no expiration
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        ...
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache
        
        Args:
            key: The cache key
            
        Returns:
            Any: The stored value (JSON deserialized), None if not found or expired
        """
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if deleted successfully, False if key didn't exist
        """
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if key exists and not expired, False otherwise
        """
        ...
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get the remaining TTL of a key
        
        Args:
            key: The cache key
            
        Returns:
            int: Remaining TTL in seconds, None if key doesn't exist or has no expiration
        """
        ...
    
    async def keys(self, pattern: str) -> list[str]:
        """Get all keys matching a pattern
        
        Args:
            pattern: Pattern to match (implementation specific)
            
        Returns:
            list[str]: List of matching keys
        """
        ...
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern
        
        Args:
            pattern: Pattern to match
            
        Returns:
            int: Number of keys deleted
        """
        ...
