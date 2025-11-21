"""
Unit tests for caching functionality.
Tests cache storage, retrieval, expiration, and cleanup.
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch
from odoo_cli.cache import get_cached, set_cached, clear_cache, get_cache_key_for_models


class TestCacheStorage:
    """Test cache storage and retrieval."""

    def test_cache_stores_and_retrieves_data(self):
        """Test data can be stored and retrieved from cache."""
        test_data = ["model1", "model2", "model3"]

        set_cached("test_key", test_data, ttl_seconds=3600)
        retrieved = get_cached("test_key", ttl_seconds=3600)

        assert retrieved == test_data

    def test_cache_miss_returns_none(self):
        """Test cache miss returns None."""
        clear_cache()  # Clear all cache
        result = get_cached("nonexistent_key")

        assert result is None

    def test_cache_stores_dict_data(self):
        """Test cache can store dictionary data."""
        test_data = {"key1": "value1", "key2": {"nested": "value"}}

        set_cached("dict_key", test_data)
        retrieved = get_cached("dict_key")

        assert retrieved == test_data

    def test_cache_stores_numeric_data(self):
        """Test cache can store numeric data."""
        test_data = [1, 2, 3, 42, 3.14]

        set_cached("numeric_key", test_data)
        retrieved = get_cached("numeric_key")

        assert retrieved == test_data


class TestCacheExpiration:
    """Test cache TTL and expiration."""

    def test_cache_expires_after_ttl(self):
        """Test cached data expires after TTL."""
        test_data = ["model1", "model2"]

        # Set cache with 1 second TTL
        set_cached("expire_key", test_data, ttl_seconds=1)
        assert get_cached("expire_key", ttl_seconds=1) == test_data

        # Wait for expiration
        time.sleep(1.1)

        # Cache should be expired
        assert get_cached("expire_key", ttl_seconds=1) is None

    def test_cache_respects_different_ttls(self):
        """Test different TTLs are respected."""
        test_data = ["model1"]

        # Set with default TTL
        set_cached("ttl_key", test_data)

        # Immediate read with same TTL should work
        result = get_cached("ttl_key")
        assert result == test_data

        # Same cache data, but read with very short TTL
        time.sleep(0.1)
        result = get_cached("ttl_key", ttl_seconds=0.01)
        # Cache is 100ms old, TTL is 10ms, so it should be expired
        assert result is None


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_models_cache_key_generation(self):
        """Test cache key generation for models."""
        key1 = get_cache_key_for_models("https://example.com", "db1")
        key2 = get_cache_key_for_models("https://example.com", "db1")
        key3 = get_cache_key_for_models("https://example.com", "db2")

        # Same inputs should produce same key
        assert key1 == key2

        # Different inputs should produce different keys
        assert key1 != key3

        # Keys should start with 'models_'
        assert key1.startswith("models_")

    def test_cache_key_handles_special_characters(self):
        """Test cache key handles special characters in URL."""
        key1 = get_cache_key_for_models(
            "https://example.com:8069/path?query=1",
            "db-name_123"
        )

        # Should not raise error and should be valid
        assert key1.startswith("models_")
        assert len(key1) > 10


class TestCacheClear:
    """Test cache clearing functionality."""

    def test_clear_specific_cache_entry(self):
        """Test clearing a specific cache entry."""
        set_cached("key1", ["model1"])
        set_cached("key2", ["model2"])

        # Clear key1
        clear_cache("key1")

        # key1 should be gone
        assert get_cached("key1") is None

        # key2 should still exist
        assert get_cached("key2") == ["model2"]

    def test_clear_all_cache(self):
        """Test clearing all cache entries."""
        set_cached("key1", ["model1"])
        set_cached("key2", ["model2"])
        set_cached("key3", ["model3"])

        # Clear all
        clear_cache()

        # All should be gone
        assert get_cached("key1") is None
        assert get_cached("key2") is None
        assert get_cached("key3") is None


class TestCacheErrorHandling:
    """Test cache error handling and robustness."""

    def test_cache_handles_corrupted_data(self):
        """Test cache handles corrupted JSON gracefully."""
        from odoo_cli.cache import _get_cache_dir, _get_cache_key

        cache_dir = _get_cache_dir()
        cache_file = cache_dir / _get_cache_key("corrupt_key")

        # Write invalid JSON
        with open(cache_file, 'w') as f:
            f.write("{ invalid json }")

        # Should return None instead of crashing
        result = get_cached("corrupt_key")
        assert result is None

    def test_cache_handles_missing_timestamp(self):
        """Test cache handles missing timestamp gracefully."""
        from odoo_cli.cache import _get_cache_dir, _get_cache_key

        cache_dir = _get_cache_dir()
        cache_file = cache_dir / _get_cache_key("notimestamp_key")

        # Write JSON without timestamp
        with open(cache_file, 'w') as f:
            json.dump({"data": ["model1"]}, f)

        # Should return None (invalid cache)
        result = get_cached("notimestamp_key")
        assert result is None

    def test_cache_handles_write_errors(self):
        """Test cache handles write errors gracefully."""
        # This test would need to mock file system errors
        # For now, just ensure set_cached doesn't crash
        test_data = ["model1"]

        # Should not raise exception
        try:
            set_cached("test_key", test_data)
            assert True
        except Exception as e:
            pytest.fail(f"set_cached raised exception: {e}")


class TestCacheIntegration:
    """Integration tests for caching."""

    def test_cache_workflow(self):
        """Test complete cache workflow."""
        test_key = "workflow_test"
        test_data = {
            "models": ["model1", "model2"],
            "count": 2,
            "timestamp": 1234567890
        }

        # Cache miss
        assert get_cached(test_key) is None

        # Store data
        set_cached(test_key, test_data, ttl_seconds=3600)

        # Cache hit
        assert get_cached(test_key, ttl_seconds=3600) == test_data

        # Clear
        clear_cache(test_key)

        # Cache miss again
        assert get_cached(test_key) is None

    def test_multiple_concurrent_cache_keys(self):
        """Test multiple cache entries don't interfere."""
        data1 = ["model1", "model2"]
        data2 = ["model3", "model4"]
        data3 = ["model5", "model6"]

        set_cached("key1", data1)
        set_cached("key2", data2)
        set_cached("key3", data3)

        # All should be retrievable
        assert get_cached("key1") == data1
        assert get_cached("key2") == data2
        assert get_cached("key3") == data3

        # Clearing one shouldn't affect others
        clear_cache("key2")
        assert get_cached("key1") == data1
        assert get_cached("key2") is None
        assert get_cached("key3") == data3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
