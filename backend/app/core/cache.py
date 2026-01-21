"""
Caching utilities for large repositories
"""

import json
import hashlib
from typing import TypeVar, Optional, Callable, Any
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, field
import asyncio

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A single cache entry"""
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class MemoryCache:
    """
    Simple in-memory cache with TTL support.
    For production, replace with Redis.
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = asyncio.Lock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired:
                del self._cache[key]
                return None
            
            entry.hits += 1
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value in cache"""
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            
            ttl = ttl or self._default_ttl
            now = datetime.now()
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
            )
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern (prefix match)"""
        async with self._lock:
            to_delete = [k for k in self._cache if k.startswith(pattern)]
            for key in to_delete:
                del self._cache[key]
            return len(to_delete)
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entries (LRU-like)"""
        if not self._cache:
            return
        
        # Sort by last access (approximated by created_at + hits)
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: (self._cache[k].created_at, -self._cache[k].hits)
        )
        
        # Remove oldest 10%
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self._cache[key]
    
    @property
    def stats(self) -> dict:
        """Get cache statistics"""
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "total_hits": total_hits,
            "default_ttl": self._default_ttl,
        }


# Global cache instance
cache = MemoryCache()


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    cache_instance: Optional[MemoryCache] = None,
):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached(ttl=60, key_prefix="my_func")
        async def my_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _cache = cache_instance or cache
            
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()[:32]
            
            # Try to get from cache
            cached_value = await _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await _cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ============ Snapshot-specific Cache Keys ============

def snapshot_cache_key(snapshot_id: str, resource: str) -> str:
    """Generate a cache key for snapshot-related data"""
    return f"snapshot:{snapshot_id}:{resource}"


async def invalidate_snapshot_cache(snapshot_id: str) -> int:
    """Invalidate all cache entries for a snapshot"""
    return await cache.invalidate_pattern(f"snapshot:{snapshot_id}:")


# ============ File Tree Cache ============

class FileTreeCache:
    """Specialized cache for file tree data"""
    
    def __init__(self, base_cache: Optional[MemoryCache] = None):
        self._cache = base_cache or cache
    
    async def get_tree(self, snapshot_id: str) -> Optional[dict]:
        """Get cached file tree"""
        key = snapshot_cache_key(snapshot_id, "tree")
        return await self._cache.get(key)
    
    async def set_tree(self, snapshot_id: str, tree: dict, ttl: int = 3600) -> None:
        """Cache file tree (default 1 hour TTL)"""
        key = snapshot_cache_key(snapshot_id, "tree")
        await self._cache.set(key, tree, ttl)
    
    async def invalidate(self, snapshot_id: str) -> bool:
        """Invalidate tree cache for a snapshot"""
        key = snapshot_cache_key(snapshot_id, "tree")
        return await self._cache.delete(key)


# Global file tree cache
file_tree_cache = FileTreeCache()
