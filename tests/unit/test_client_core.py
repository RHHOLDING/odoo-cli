"""
Unit tests for JSON-RPC client core functionality.
Tests client initialization, configuration, and basic operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from odoo_cli.client import OdooClient, retry_on_network_error
import requests


class TestOdooClientInit:
    """Test OdooClient initialization and configuration."""

    def test_client_init_with_https(self):
        """Test client initialization with https URL."""
        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        assert client.url == "https://example.com"
        assert client.db == "test_db"
        assert client.username == "admin"
        assert client.timeout == 30
        assert client.verify_ssl is True

    def test_client_init_without_protocol(self):
        """Test client auto-adds https:// if missing."""
        client = OdooClient(
            url="example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        assert client.url == "https://example.com"

    def test_client_strips_trailing_slash(self):
        """Test client removes trailing slash from URL."""
        client = OdooClient(
            url="https://example.com/",
            db="test_db",
            username="admin",
            password="password"
        )
        assert client.url == "https://example.com"

    def test_client_session_created(self):
        """Test that requests.Session is created."""
        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        assert isinstance(client.session, requests.Session)

    def test_client_custom_timeout(self):
        """Test client with custom timeout."""
        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password",
            timeout=60
        )
        assert client.timeout == 60

    def test_client_ssl_verification_disabled(self):
        """Test client with SSL verification disabled."""
        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password",
            verify_ssl=False
        )
        assert client.verify_ssl is False


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def test_retry_succeeds_on_first_call(self):
        """Test retry decorator when function succeeds immediately."""
        mock_func = Mock(return_value="success")

        @retry_on_network_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test retry decorator recovers after transient failures."""
        mock_func = Mock(
            side_effect=[
                requests.exceptions.ConnectionError("error"),
                requests.exceptions.ConnectionError("error"),
                "success"
            ]
        )

        @retry_on_network_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_exhausts_max_retries(self):
        """Test retry decorator raises after max retries."""
        mock_func = Mock(side_effect=requests.exceptions.ConnectionError("error"))

        @retry_on_network_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(requests.exceptions.ConnectionError):
            test_func()

        assert mock_func.call_count == 3

    def test_retry_does_not_retry_value_error(self):
        """Test retry decorator does not retry non-network errors."""
        mock_func = Mock(side_effect=ValueError("not a network error"))

        @retry_on_network_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(ValueError):
            test_func()

        assert mock_func.call_count == 1


class TestClientExecute:
    """Test client execute method."""

    @patch.object(OdooClient, '_jsonrpc_call')
    @patch.object(OdooClient, '_ensure_connected')
    def test_execute_calls_jsonrpc(self, mock_ensure, mock_jsonrpc):
        """Test execute method calls _jsonrpc_call correctly."""
        mock_jsonrpc.return_value = "result"

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        result = client.execute("res.partner", "search_count", [])

        assert result == "result"
        mock_ensure.assert_called_once()
        mock_jsonrpc.assert_called_once()

    @patch.object(OdooClient, '_execute')
    def test_search_wraps_domain(self, mock_execute):
        """Test search method wraps domain in list."""
        mock_execute.return_value = [1, 2, 3]

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        domain = [["id", "=", 1]]
        result = client.search("res.partner", domain)

        assert result == [1, 2, 3]
        # Verify domain was wrapped in list for execute_kw
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        # search() should call _execute(model, 'search', [domain], **kwargs)
        assert call_args[0][0] == "res.partner"  # model
        assert call_args[0][1] == "search"  # method
        assert call_args[0][2] == [domain]  # domain wrapped in list

    @patch.object(OdooClient, '_execute')
    def test_read_method(self, mock_execute):
        """Test read method."""
        mock_execute.return_value = [{"id": 1, "name": "Test"}]

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        result = client.read("res.partner", [1], fields=["name"])

        assert result == [{"id": 1, "name": "Test"}]
        mock_execute.assert_called_once()

    @patch.object(OdooClient, '_execute')
    def test_search_read_method(self, mock_execute):
        """Test search_read method."""
        mock_execute.return_value = [{"id": 1, "name": "Test"}]

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        result = client.search_read("res.partner", [], fields=["name"], limit=10)

        assert result == [{"id": 1, "name": "Test"}]
        mock_execute.assert_called_once()


class TestClientCaching:
    """Test client caching functionality."""

    @patch('odoo_cli.cache.get_cached')
    @patch('odoo_cli.cache.set_cached')
    @patch.object(OdooClient, '_execute')
    def test_get_models_uses_cache(self, mock_execute, mock_set_cache, mock_get_cache):
        """Test get_models uses cache when available."""
        mock_get_cache.return_value = ["model1", "model2"]
        mock_execute.return_value = []

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        result = client.get_models()

        assert result == ["model1", "model2"]
        # Should not call _execute if cache hit
        mock_execute.assert_not_called()
        mock_get_cache.assert_called_once()

    @patch('odoo_cli.cache.get_cached')
    @patch('odoo_cli.cache.set_cached')
    @patch.object(OdooClient, '_execute')
    def test_get_models_fetches_when_cache_miss(self, mock_execute, mock_set_cache, mock_get_cache):
        """Test get_models fetches from server on cache miss."""
        mock_get_cache.return_value = None  # Cache miss
        mock_execute.side_effect = [
            [1, 2],  # search returns IDs
            [{"model": "model1"}, {"model": "model2"}]  # read returns records
        ]

        client = OdooClient(
            url="https://example.com",
            db="test_db",
            username="admin",
            password="password"
        )
        client.uid = 1

        result = client.get_models()

        assert result == ["model1", "model2"]
        assert mock_execute.call_count == 2
        mock_set_cache.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
