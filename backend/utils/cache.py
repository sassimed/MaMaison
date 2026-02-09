"""
Cache module for MyDar API
Simple in-memory cache with TTL support
"""

import asyncio
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
import json

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            item = self._cache[key]
            if item["expires_at"] > time.time():
                return item["value"]
            else:
                # Expired - remove it
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL (default 5 minutes)"""
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
    
    async def delete(self, key: str) -> None:
        """Delete a specific key"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (simple contains match)"""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries"""
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._cache.items() if v["expires_at"] <= now]
            for key in expired:
                del self._cache[key]
            return len(expired)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = time.time()
        valid = sum(1 for v in self._cache.values() if v["expires_at"] > now)
        expired = len(self._cache) - valid
        return {
            "total_keys": len(self._cache),
            "valid_keys": valid,
            "expired_keys": expired
        }


# Global cache instance
cache = InMemoryCache()


def make_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, prefix: str = ""):
    """
    Decorator to cache async function results
    
    Usage:
        @cached(ttl=600, prefix="categories")
        async def get_categories():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{prefix}:{func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        
        # Add method to invalidate this function's cache
        wrapper.invalidate = lambda: cache.delete_pattern(f"{prefix}:{func.__name__}")
        wrapper.cache_key_prefix = f"{prefix}:{func.__name__}"
        
        return wrapper
    return decorator


# Cache TTL constants (in seconds)
class CacheTTL:
    VERY_SHORT = 30      # 30 seconds - for rapidly changing data
    SHORT = 60           # 1 minute
    MEDIUM = 300         # 5 minutes
    LONG = 600           # 10 minutes
    VERY_LONG = 1800     # 30 minutes
    HOUR = 3600          # 1 hour
    DAY = 86400          # 24 hours


# Background task to cleanup expired cache entries
async def cache_cleanup_task():
    """Periodic cleanup of expired cache entries"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        cleaned = await cache.cleanup_expired()
        if cleaned > 0:
            print(f"[Cache] Cleaned up {cleaned} expired entries")
