"""
File-based response caching with TTL support.

Provides simple caching for frequently accessed data like model definitions.
Cache is stored as JSON files in ~/.odoo-cli/cache/ with automatic expiration.
"""

import json
import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _get_cache_dir() -> Path:
    """Get or create the cache directory."""
    cache_dir = Path.home() / ".odoo-cli" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_key(key: str) -> str:
    """Generate a safe filename from a cache key."""
    # Hash the key to avoid filesystem issues with special characters
    hash_value = hashlib.md5(key.encode()).hexdigest()
    return f"cache_{hash_value}.json"


def get_cached(cache_key: str, ttl_seconds: int = 86400) -> Optional[Any]:
    """
    Retrieve cached data if it exists and hasn't expired.

    Args:
        cache_key: Identifier for the cached data (e.g., 'models_db_url_hash')
        ttl_seconds: Time to live in seconds (default: 24 hours = 86400)

    Returns:
        Cached data if found and valid, None otherwise
    """
    try:
        cache_dir = _get_cache_dir()
        cache_file = cache_dir / _get_cache_key(cache_key)

        if not cache_file.exists():
            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        # Read cache file
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)

        # Check TTL
        stored_time = cache_data.get('_timestamp')
        if not stored_time:
            logger.debug(f"Cache invalid (no timestamp): {cache_key}")
            cache_file.unlink()  # Delete invalid cache
            return None

        age = time.time() - stored_time
        if age > ttl_seconds:
            logger.debug(f"Cache expired for {cache_key} (age: {age:.1f}s, TTL: {ttl_seconds}s)")
            cache_file.unlink()  # Delete expired cache
            return None

        # Cache is valid
        logger.debug(f"Cache hit for {cache_key} (age: {age:.1f}s)")
        return cache_data.get('data')

    except Exception as e:
        logger.warning(f"Error reading cache for {cache_key}: {str(e)}")
        return None


def set_cached(cache_key: str, data: Any, ttl_seconds: int = 86400) -> None:
    """
    Store data in cache with TTL.

    Args:
        cache_key: Identifier for the cached data
        data: Data to cache (must be JSON serializable)
        ttl_seconds: Time to live in seconds (default: 24 hours = 86400)
    """
    try:
        cache_dir = _get_cache_dir()
        cache_file = cache_dir / _get_cache_key(cache_key)

        # Create cache entry with timestamp
        cache_entry = {
            '_timestamp': time.time(),
            'data': data
        }

        # Write cache file
        with open(cache_file, 'w') as f:
            json.dump(cache_entry, f)

        logger.debug(f"Cached data for {cache_key} (TTL: {ttl_seconds}s)")

    except Exception as e:
        logger.warning(f"Error writing cache for {cache_key}: {str(e)}")
        # Caching failure should not crash the application


def clear_cache(cache_key: Optional[str] = None) -> None:
    """
    Clear cache entries.

    Args:
        cache_key: Specific cache key to clear. If None, clears all cache.
    """
    try:
        cache_dir = _get_cache_dir()

        if cache_key:
            # Clear specific entry
            cache_file = cache_dir / _get_cache_key(cache_key)
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Cleared cache for {cache_key}")
        else:
            # Clear all cache
            if cache_dir.exists():
                for cache_file in cache_dir.glob("cache_*.json"):
                    cache_file.unlink()
                logger.debug("Cleared all cache")

    except Exception as e:
        logger.warning(f"Error clearing cache: {str(e)}")


def get_cache_key_for_models(url: str, db: str) -> str:
    """
    Generate a cache key for model definitions.

    Args:
        url: Odoo server URL
        db: Database name

    Returns:
        Cache key string
    """
    # Create a hash from url and db to avoid key length issues
    key_material = f"{url}:{db}"
    key_hash = hashlib.md5(key_material.encode()).hexdigest()
    return f"models_{key_hash}"
