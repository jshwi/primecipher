"""Tests for search cache functionality."""

from unittest.mock import MagicMock, patch

from backend.adapters.source import (
    Source,
    _get_search_cached,
    _set_search_cached,
    clear_search_cache,
)


class TestSearchCache:
    """Test search cache functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        clear_search_cache()

    def test_search_cache_basic_functionality(self) -> None:
        """Test basic cache get/set functionality."""
        # Test cache miss
        assert _get_search_cached("bitcoin") is None

        # Test cache set and hit
        _set_search_cached("bitcoin", ["bitcoin", "wrapped-bitcoin"])
        cached_result = _get_search_cached("bitcoin")
        assert cached_result == ["bitcoin", "wrapped-bitcoin"]

        # Test case insensitive
        assert _get_search_cached("BITCOIN") == ["bitcoin", "wrapped-bitcoin"]
        assert _get_search_cached("  Bitcoin  ") == [
            "bitcoin",
            "wrapped-bitcoin",
        ]

    def test_search_cache_ttl_expiry(self) -> None:
        """Test cache TTL expiry."""
        # Mock time to control TTL
        with patch("backend.adapters.source._now") as mock_now:
            # Set initial time
            mock_now.return_value = 1000.0
            _set_search_cached("bitcoin", ["bitcoin"])
            assert _get_search_cached("bitcoin") == ["bitcoin"]

            # Advance time beyond TTL (15 minutes = 900 seconds)
            mock_now.return_value = 1901.0
            assert _get_search_cached("bitcoin") is None

    def test_clear_search_cache(self) -> None:
        """Test cache clearing functionality."""
        _set_search_cached("bitcoin", ["bitcoin"])
        _set_search_cached("ethereum", ["ethereum"])

        assert _get_search_cached("bitcoin") == ["bitcoin"]
        assert _get_search_cached("ethereum") == ["ethereum"]

        clear_search_cache()

        assert _get_search_cached("bitcoin") is None
        assert _get_search_cached("ethereum") is None

    @patch("backend.adapters.source._get_json")
    def test_search_coins_uses_cache(self, mock_get_json: MagicMock) -> None:
        """Test that _search_coins uses cache to avoid duplicate HTTP calls.

        :param mock_get_json: Mock for _get_json function.
        """
        # Mock search response
        mock_get_json.return_value = {
            "coins": [
                {"name": "Bitcoin", "id": "bitcoin"},
                {"name": "Wrapped Bitcoin", "id": "wrapped-bitcoin"},
            ],
        }

        source = Source("coingecko")
        adapter = source._impl

        # Clear cache to ensure clean state
        clear_search_cache()

        # First call should make HTTP request
        result1 = adapter._search_coins(["bitcoin"])

        assert "bitcoin" in result1
        assert "wrapped-bitcoin" in result1
        assert mock_get_json.call_count == 1  # 1 HTTP call

        # Second call should use cache (no HTTP call)
        result2 = adapter._search_coins(["bitcoin"])

        assert result1 == result2  # Same results
        assert (
            mock_get_json.call_count == 1
        )  # Still only 1 call (no new calls)

    @patch("backend.adapters.source._get_json")
    def test_search_coins_multiple_terms_caching(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test caching behavior with multiple terms.

        :param mock_get_json: Mock for _get_json function.
        """

        # Mock different responses for different terms
        def mock_get_json_side_effect(
            _url: str,
            params: dict | None = None,
        ) -> dict:
            if "bitcoin" in (params or {}).get("query", ""):
                return {
                    "coins": [
                        {"name": "Bitcoin", "id": "bitcoin"},
                        {"name": "Wrapped Bitcoin", "id": "wrapped-bitcoin"},
                    ],
                }
            if "ethereum" in (params or {}).get("query", ""):
                return {
                    "coins": [
                        {"name": "Ethereum", "id": "ethereum"},
                        {"name": "Wrapped Ethereum", "id": "wrapped-ethereum"},
                    ],
                }
            return {"coins": []}

        mock_get_json.side_effect = mock_get_json_side_effect

        source = Source("coingecko")
        adapter = source._impl

        # Clear cache to ensure clean state
        clear_search_cache()

        # First call with both terms - should make 2 HTTP calls
        result1 = adapter._search_coins(["bitcoin", "ethereum"])

        assert "bitcoin" in result1
        assert "ethereum" in result1
        assert mock_get_json.call_count == 2  # 2 HTTP calls

        # Second call with same terms - should use cache (no HTTP calls)
        result2 = adapter._search_coins(["bitcoin", "ethereum"])

        assert result1 == result2  # Same results
        assert (
            mock_get_json.call_count == 2
        )  # Still only 2 calls (no new calls)

        # Third call with mixed terms - should use cache for bitcoin,
        # HTTP for litecoin
        def mock_get_json_side_effect_with_litecoin(
            _url: str,
            params: dict | None = None,
        ) -> dict:
            if "litecoin" in (params or {}).get("query", ""):
                return {
                    "coins": [
                        {"name": "Litecoin", "id": "litecoin"},
                    ],
                }
            return mock_get_json_side_effect(_url, params)

        mock_get_json.side_effect = mock_get_json_side_effect_with_litecoin

        result3 = adapter._search_coins(["bitcoin", "litecoin"])

        assert "bitcoin" in result3  # From cache
        assert "litecoin" in result3  # From HTTP
        assert "ethereum" not in result3  # Not requested

        # Verify total calls: 2 initial + 1 for litecoin = 3
        assert mock_get_json.call_count == 3

    @patch("backend.adapters.source._get_json")
    def test_search_coins_cache_logging(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test that cache hits are logged appropriately.

        :param mock_get_json: Mock for _get_json function.
        """
        mock_get_json.return_value = {
            "coins": [{"name": "Bitcoin", "id": "bitcoin"}],
        }

        source = Source("coingecko")
        adapter = source._impl

        # Clear cache to ensure clean state
        clear_search_cache()

        with patch("backend.adapters.source.logger") as mock_logger:
            # First call - should not log cache hit
            adapter._search_coins(["bitcoin"])
            cache_hit_calls = [
                call
                for call in mock_logger.debug.call_args_list
                if "cache hit" in str(call)
            ]
            assert len(cache_hit_calls) == 0

            # Second call - should log cache hit
            adapter._search_coins(["bitcoin"])
            cache_hit_calls = [
                call
                for call in mock_logger.debug.call_args_list
                if "cache hit" in str(call)
            ]
            assert len(cache_hit_calls) == 1
            # Check the actual call arguments
            call_args = cache_hit_calls[0][0]
            assert "cache hit for term: %s" in call_args[0]
            assert call_args[1] == "bitcoin"

    @patch("backend.adapters.source._get_json")
    def test_search_coins_caching_logging(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test that cache storage is logged appropriately.

        :param mock_get_json: Mock for _get_json function.
        """
        mock_get_json.return_value = {
            "coins": [
                {"name": "Bitcoin", "id": "bitcoin"},
                {"name": "Wrapped Bitcoin", "id": "wrapped-bitcoin"},
            ],
        }

        source = Source("coingecko")
        adapter = source._impl

        # Clear cache to ensure clean state
        clear_search_cache()

        with patch("backend.adapters.source.logger") as mock_logger:
            adapter._search_coins(["bitcoin"])

            # Should log cache storage
            cache_log_calls = [
                call
                for call in mock_logger.debug.call_args_list
                if "cached" in str(call) and "ids for term" in str(call)
            ]
            assert len(cache_log_calls) == 1
            # Check the actual call arguments
            call_args = cache_log_calls[0][0]
            assert "cached %d ids for term: %s" in call_args[0]
            assert call_args[1] == 2  # Number of IDs
            assert call_args[2] == "bitcoin"  # Term
