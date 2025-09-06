"""Tests for missing coverage in source.py module."""

import time
from unittest.mock import MagicMock, patch

import requests

from backend.adapters.source import TokenBucket, _get_json


class TestTokenBucketCoverage:
    """Test TokenBucket.acquire() method for missing coverage."""

    def test_acquire_waits_when_no_tokens(self) -> None:
        """Test that acquire() waits when no tokens are available."""
        # Create bucket with very low rate (1 token per 10 seconds)
        bucket = TokenBucket(rps=0.1, burst=1)

        # Consume the initial token
        bucket.acquire()

        # Now bucket should be empty, next acquire should wait
        start_time = time.monotonic()
        bucket.acquire()
        elapsed = time.monotonic() - start_time

        # Should have waited approximately 10 seconds
        assert elapsed >= 9.0  # Allow some tolerance for test execution time

    def test_acquire_refills_tokens_over_time(self) -> None:
        """Test that tokens are refilled based on elapsed time."""
        bucket = TokenBucket(rps=1.0, burst=2)

        # Consume both tokens
        bucket.acquire()
        bucket.acquire()

        # Wait 1 second
        time.sleep(1.1)

        # Should be able to acquire again
        start_time = time.monotonic()
        bucket.acquire()
        elapsed = time.monotonic() - start_time

        # Should not have waited long since token was refilled
        assert elapsed < 0.5


class TestGetJsonCoverage:
    """Test _get_json() method for missing coverage."""

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_429_with_retry_after_header(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test 429 handling with Retry-After header."""
        # Mock response with 429 status and Retry-After header
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "2"}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        # Mock successful response on retry
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"success": True}

        mock_session.get.side_effect = [mock_response, mock_response2]

        result = _get_json("https://api.example.com/test")

        # Should have slept for 2 seconds due to Retry-After header
        # (plus jitter, so check that 2 is in the call args)
        sleep_calls = [
            call for call in _mock_sleep.call_args_list if call[0][0] == 2
        ]
        assert (
            len(sleep_calls) > 0
        ), f"Expected sleep(2) call, got calls: {_mock_sleep.call_args_list}"
        assert result == {"success": True}

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_429_without_retry_after_header(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test 429 handling without Retry-After header."""
        # Mock response with 429 status but no Retry-After header
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        # Mock successful response on retry
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"success": True}

        mock_session.get.side_effect = [mock_response, mock_response2]

        result = _get_json("https://api.example.com/test")

        # Should have used exponential backoff
        _mock_sleep.assert_called()
        assert result == {"success": True}

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_5xx_server_error_retry(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test 5xx server error handling with retry."""
        # Mock 500 error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        # Mock successful response on retry
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"success": True}

        mock_session.get.side_effect = [mock_response, mock_response2]

        result = _get_json("https://api.example.com/test")

        # Should have used exponential backoff for 5xx error
        _mock_sleep.assert_called()
        assert result == {"success": True}

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_5xx_last_attempt_no_sleep(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test 5xx error on last attempt doesn't sleep."""
        # Mock 500 error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        mock_session.get.return_value = mock_response

        result = _get_json("https://api.example.com/test")

        # Should not sleep on last attempt
        assert result is None

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_request_exception_retry(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test RequestException handling with retry."""
        # Mock RequestException on first call
        mock_session.get.side_effect = [
            requests.RequestException("Network error"),
            MagicMock(status_code=200, json=lambda: {"success": True}),
        ]

        result = _get_json("https://api.example.com/test")

        # Should have retried with backoff
        _mock_sleep.assert_called()
        assert result == {"success": True}

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_all_attempts_fail(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test when all attempts fail."""
        # Mock RequestException on all calls
        mock_session.get.side_effect = requests.RequestException(
            "Network error",
        )

        result = _get_json("https://api.example.com/test")

        # Should return None after all attempts fail
        assert result is None

    @patch("backend.adapters.source.sess")
    @patch("backend.adapters.source._cg_limiter")
    @patch("time.sleep")
    def test_get_json_exhausts_attempts_returns_none(
        self,
        _mock_sleep: MagicMock,
        _mock_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test that _get_json returns None when all attempts are exhausted."""
        # Mock 429 error on all calls to exhaust all attempts
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        mock_session.get.return_value = mock_response

        result = _get_json("https://api.example.com/test")

        # Should return None after exhausting all attempts
        assert result is None


class TestCoinGeckoAdapterCoverage:
    """Test CoinGecko adapter methods for missing coverage."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        from backend.adapters.source import _make_cg

        self.adapter = _make_cg()

    @patch("backend.adapters.source._get_json")
    def test_search_coins_non_dict_response(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _search_coins handles non-dict response."""
        # Mock non-dict response (list instead of dict)
        mock_get_json.return_value = [{"name": "Bitcoin", "id": "bitcoin"}]

        coin_ids = self.adapter._search_coins(["bitcoin"])

        # Should handle gracefully and return empty list
        assert not coin_ids

    @patch("backend.adapters.source._get_json")
    def test_search_coins_exception_handling(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _search_coins exception handling."""
        # Mock exception on API call
        mock_get_json.side_effect = Exception("API Error")

        coin_ids = self.adapter._search_coins(["bitcoin"])

        # Should handle exception and return empty list
        assert not coin_ids

    @patch("backend.adapters.source._get_json")
    def test_search_coins_all_terms_fail_warning(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _search_coins logs warning when all terms fail."""
        # Mock exception on all API calls
        mock_get_json.side_effect = Exception("API Error")

        with patch("backend.adapters.source.logger") as mock_logger:
            coin_ids = self.adapter._search_coins(["bitcoin", "ethereum"])

            # Should log warning about all terms failing
            mock_logger.warning.assert_called_once()
            assert not coin_ids

    @patch("backend.adapters.source._get_json")
    def test_get_market_data_exception_handling(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _get_market_data exception handling."""
        # Mock exception on API call
        mock_get_json.side_effect = Exception("API Error")

        result = self.adapter._get_market_data(["bitcoin"])

        # Should handle exception and return empty list
        assert not result

    def test_map_market_to_items_empty_data(self) -> None:
        """Test _map_market_to_items with empty data."""
        result = self.adapter._map_market_to_items([])

        # Should return empty list
        assert not result

    def test_fetch_parents_method(self) -> None:
        """Test fetch_parents method calls parents_for."""
        with patch.object(self.adapter, "parents_for") as mock_parents_for:
            mock_parents_for.return_value = [{"parent": "test"}]

            result = self.adapter.fetch_parents("test", ["bitcoin"])

            # Should call parents_for with same arguments
            mock_parents_for.assert_called_once_with("test", ["bitcoin"])
            assert result == [{"parent": "test"}]


class TestDexscreenerCoverage:
    """Test coverage for parents_for_dexscreener function."""

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_basic(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test basic functionality of parents_for_dexscreener."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Test Token",
                        "symbol": "TEST",
                        "address": "0x123",
                    },
                    "chainId": "ethereum",
                    "priceUsd": "1.5",
                    "volume": {"h24": "1000.0"},
                    "fdv": "50000.0",
                    "liquidity": {"usd": "25000.0"},
                    "url": "https://test.com",
                },
            ],
        }

        result = parents_for_dexscreener("test", ["bitcoin"])

        # Should return properly formatted results
        assert len(result) == 1
        assert result[0]["parent"] == "Test Token"
        assert result[0]["symbol"] == "TEST"
        assert result[0]["price"] == 1.5
        assert result[0]["vol24h"] == 1000.0
        assert result[0]["source"] == "dexscreener"

    @patch("backend.adapters.source._get_json")
    def test_parents_for_dexscreener_empty_terms(
        self,
        mock_get_json: MagicMock,
    ) -> None:
        """Test parents_for_dexscreener with empty/invalid terms."""
        from backend.adapters.source import parents_for_dexscreener

        # Test with generic terms that should be filtered out
        result = parents_for_dexscreener("test", ["swap", "defi", "ab"])

        # Should return empty list without making API calls
        assert not result
        mock_get_json.assert_not_called()

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_api_error(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test parents_for_dexscreener handles API errors."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API error
        mock_get_json.side_effect = Exception("API Error")

        result = parents_for_dexscreener("test", ["bitcoin"])

        # Should handle error and return empty list
        assert not result

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_deduplication(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test deduplication logic in parents_for_dexscreener."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with duplicate addresses
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Test Token",
                        "symbol": "TEST",
                        "address": "0x123",
                    },
                    "chainId": "ethereum",
                    "volume": {"h24": "1000.0"},
                },
                {
                    "baseToken": {
                        "name": "Test Token 2",
                        "symbol": "TEST2",
                        "address": "0x123",  # Same address
                    },
                    "chainId": "ethereum",  # Same chain
                    "volume": {"h24": "2000.0"},  # Higher volume
                },
            ],
        }

        result = parents_for_dexscreener("test", ["bitcoin"])

        # Should keep only the one with higher volume
        assert len(result) == 1
        assert result[0]["parent"] == "Test Token 2"
        assert result[0]["vol24h"] == 2000.0

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_edge_cases(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test edge cases in parents_for_dexscreener."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with various edge cases
        mock_get_json.side_effect = [
            None,  # First call returns None
            {"pairs": []},  # Second call returns empty pairs
            {  # Third call returns data with missing fields
                "pairs": [
                    {
                        "baseToken": {},  # Empty base token
                    },
                    {
                        "baseToken": {
                            "name": "Test Token",
                            "symbol": "TEST",
                            "address": "0x123",
                        },
                        "chainId": "ethereum",
                        # Missing price, volume, etc.
                    },
                    {
                        "baseToken": {
                            "symbol": "TEST2",  # No name, use symbol
                            "address": "0x456",
                        },
                        "chainId": "ethereum",
                        "priceUsd": "invalid",  # Invalid price
                        "volume": {"h24": "invalid"},  # Invalid volume
                        "fdv": "invalid",  # Invalid fdv
                        "liquidity": {"usd": "invalid"},  # Invalid liquidity
                        "pairAddress": "0x789",  # Use pairAddress as fallback
                    },
                ],
            },
        ]

        result = parents_for_dexscreener(
            "test",
            ["bitcoin", "ethereum", "solana"],
        )

        # Should handle all edge cases and return valid results
        assert len(result) == 2
        # Check that both tokens are present
        parents = [r["parent"] for r in result]
        assert "Test Token" in parents
        assert "TEST2" in parents
        # Check that the TEST2 token uses address as fallback
        test2_token = next(r for r in result if r["parent"] == "TEST2")
        assert test2_token["address"] == "0x456"

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_liquidity_scoring(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test liquidity-based scoring in parents_for_dexscreener."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with no volume but liquidity
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Token A",
                        "symbol": "A",
                        "address": "0x123",
                    },
                    "chainId": "ethereum",
                    "liquidity": {"usd": "10000.0"},
                },
                {
                    "baseToken": {
                        "name": "Token B",
                        "symbol": "B",
                        "address": "0x456",
                    },
                    "chainId": "ethereum",
                    "liquidity": {"usd": "20000.0"},
                },
            ],
        }

        result = parents_for_dexscreener("test", ["test"])

        # Should score based on liquidity
        assert len(result) == 2
        assert result[0]["parent"] == "Token B"  # Higher liquidity first
        assert result[0]["matches"] == 100
        assert result[1]["parent"] == "Token A"
        assert result[1]["matches"] == 50

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_fallback_scoring(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test fallback scoring in parents_for_dexscreener."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with no volume or liquidity
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Token A",
                        "symbol": "A",
                        "address": "0x123",
                    },
                    "chainId": "ethereum",
                },
            ],
        }

        result = parents_for_dexscreener("test", ["test"])

        # Should use fallback score of 10
        assert len(result) == 1
        assert result[0]["matches"] == 10

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_missing_fields_coverage(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test coverage for missing required fields."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with missing required fields
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Token A",
                        "symbol": "A",
                        # Missing address
                    },
                    "chainId": "ethereum",
                },
                {
                    "baseToken": {
                        "name": "Token B",
                        "symbol": "B",
                        "address": "0x123",
                    },
                    # Missing chainId
                },
                {
                    # Missing name entirely
                    "baseToken": {
                        "address": "0x456",
                    },
                    "chainId": "ethereum",
                },
                {
                    "baseToken": {
                        "name": "Valid Token",
                        "symbol": "VALID",
                        "address": "0x789",
                    },
                    "chainId": "ethereum",
                    "volume24h": "5000.0",  # Use volume24h instead
                },
            ],
        }

        result = parents_for_dexscreener("test", ["test"])

        # Should only return the valid token
        assert len(result) == 1
        assert result[0]["parent"] == "Valid Token"
        assert result[0]["vol24h"] == 5000.0

    @patch("backend.adapters.source._get_json")
    @patch("backend.adapters.source.time.sleep")
    def test_parents_for_dexscreener_dedup_skip_lower_volume(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test deduplication skips lower volume entries."""
        from backend.adapters.source import parents_for_dexscreener

        # Mock API response with same address but different volumes
        mock_get_json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "name": "Token High",
                        "symbol": "HIGH",
                        "address": "0x123",
                    },
                    "chainId": "ethereum",
                    "volume": {"h24": "10000.0"},
                },
                {
                    "baseToken": {
                        "name": "Token Low",
                        "symbol": "LOW",
                        "address": "0x123",  # Same address
                    },
                    "chainId": "ethereum",  # Same chain
                    "volume": {"h24": "5000.0"},  # Lower volume
                },
            ],
        }

        result = parents_for_dexscreener("test", ["test"])

        # Should keep only the higher volume token
        assert len(result) == 1
        assert result[0]["parent"] == "Token High"
        assert result[0]["vol24h"] == 10000.0
