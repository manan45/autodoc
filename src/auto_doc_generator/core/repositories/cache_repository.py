"""
Cache repository for storing and retrieving cached data.

This repository handles caching operations to improve performance
by avoiding redundant computations.
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheRepository:
    """Repository for cache operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize cache repository.
        
        Args:
            config: Cache configuration
        """
        self.config = config or {}
        self.cache_type = self.config.get('type', 'memory')
        self.ttl_seconds = self.config.get('ttl_seconds', 3600)
        self.max_size = self.config.get('max_size', 1000)
        
        # Initialize cache storage
        if self.cache_type == 'memory':
            self._memory_cache = {}
            self._cache_timestamps = {}
        elif self.cache_type == 'file':
            self.cache_dir = Path(self.config.get('cache_dir', '.cache'))
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if self.cache_type == 'memory':
                return self._get_memory(key)
            elif self.cache_type == 'file':
                return self._get_file(key)
            else:
                logger.warning(f"Unknown cache type: {self.cache_type}")
                return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        try:
            if self.cache_type == 'memory':
                self._set_memory(key, value, ttl)
            elif self.cache_type == 'file':
                self._set_file(key, value, ttl)
            else:
                logger.warning(f"Unknown cache type: {self.cache_type}")
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
        """
        try:
            if self.cache_type == 'memory':
                self._delete_memory(key)
            elif self.cache_type == 'file':
                self._delete_file(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            if self.cache_type == 'memory':
                self._memory_cache.clear()
                self._cache_timestamps.clear()
            elif self.cache_type == 'file':
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def _get_memory(self, key: str) -> Optional[Any]:
        """Get from memory cache."""
        if key not in self._memory_cache:
            return None
        
        # Check expiration
        if key in self._cache_timestamps:
            timestamp, ttl = self._cache_timestamps[key]
            if ttl and datetime.now() > timestamp + timedelta(seconds=ttl):
                self._delete_memory(key)
                return None
        
        return self._memory_cache[key]
    
    def _set_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in memory cache."""
        # Check cache size limit
        if len(self._memory_cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self._cache_timestamps.keys(),
                key=lambda k: self._cache_timestamps[k][0]
            )
            self._delete_memory(oldest_key)
        
        self._memory_cache[key] = value
        self._cache_timestamps[key] = (datetime.now(), ttl or self.ttl_seconds)
    
    def _delete_memory(self, key: str) -> None:
        """Delete from memory cache."""
        self._memory_cache.pop(key, None)
        self._cache_timestamps.pop(key, None)
    
    def _get_file(self, key: str) -> Optional[Any]:
        """Get from file cache."""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check expiration
            if 'expires_at' in cache_data:
                if datetime.now() > cache_data['expires_at']:
                    cache_file.unlink()
                    return None
            
            return cache_data['value']
            
        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None
    
    def _set_file(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in file cache."""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        
        cache_data = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl or self.ttl_seconds)
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
    
    def _delete_file(self, key: str) -> None:
        """Delete from file cache."""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        try:
            cache_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error deleting cache file {cache_file}: {e}")
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache_type == 'memory':
            return {
                'type': 'memory',
                'size': len(self._memory_cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }
        elif self.cache_type == 'file':
            cache_files = list(self.cache_dir.glob("*.cache"))
            return {
                'type': 'file',
                'size': len(cache_files),
                'cache_dir': str(self.cache_dir),
                'ttl_seconds': self.ttl_seconds
            }
        else:
            return {'type': self.cache_type}
