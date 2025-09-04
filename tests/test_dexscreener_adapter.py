"""Tests for DexScreener adapter."""

from unittest.mock import Mock, patch

from backend.adapters.dexscreener import DexScreenerAdapter


class TestDexScreenerAdapter:
    """Test cases for DexScreenerAdapter."""

    def test_fetch_parents_empty_terms(self) -> None:
        """Test fetch_parents with empty terms list."""
        adapter = DexScreenerAdapter()
        result = adapter.fetch_parents("test", [])
        assert not result

    def test_fetch_parents_caps_terms(self) -> None:
        """Test fetch_parents caps to first 3 terms."""
        adapter = DexScreenerAdapter()

        with patch.object(adapter, "_query_dexscreener") as mock_query:
            mock_query.return_value = []

            # Test with more than 3 terms
            adapter.fetch_parents(
                "test",
                ["term1", "term2", "term3", "term4", "term5"],
            )

            # Should only call query 3 times
            assert mock_query.call_count == 3
            mock_query.assert_any_call("term1")
            mock_query.assert_any_call("term2")
            mock_query.assert_any_call("term3")

    def test_fetch_parents_rate_limiting(self) -> None:
        """Test fetch_parents applies rate limiting."""
        adapter = DexScreenerAdapter()

        with (
            patch.object(adapter, "_query_dexscreener") as mock_query,
            patch("time.sleep") as mock_sleep,
        ):
            mock_query.return_value = []

            adapter.fetch_parents("test", ["term1", "term2", "term3"])

            # Should sleep between queries (2 sleeps for 3 terms)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(0.2)

    def test_query_dexscreener_success(self) -> None:
        """Test _query_dexscreener with successful API response."""
        adapter = DexScreenerAdapter()

        mock_response = Mock()
        mock_response.json.return_value = {
            "pairs": [
                {
                    "baseToken": {
                        "address": "0x123",
                        "symbol": "TEST",
                        "name": "Test Token",
                    },
                    "volume": {"h24": 1000},
                    "pairUrl": "https://example.com/pair",
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "pairAddress": "0xpair",
                },
            ],
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            result = adapter._query_dexscreener("test")

            assert len(result) == 1
            assert result[0]["baseToken"]["symbol"] == "TEST"

    def test_query_dexscreener_api_error(self) -> None:
        """Test _query_dexscreener handles API errors."""
        adapter = DexScreenerAdapter()

        with patch("httpx.Client") as mock_client:
            # Mock the context manager to raise an httpx exception
            import httpx

            mock_client.return_value.__enter__.return_value.get.side_effect = (
                httpx.RequestError("API Error")
            )

            result = adapter._query_dexscreener("test")

            assert not result

    def test_deduplicate_pairs(self) -> None:
        """Test _deduplicate_pairs removes duplicates."""
        adapter = DexScreenerAdapter()

        pairs = [
            {
                "baseToken": {"address": "0x123", "symbol": "TEST"},
                "volume": {"h24": 1000},
            },
            {
                "baseToken": {"address": "0x123", "symbol": "TEST"},
                "volume": {"h24": 2000},
            },
            {
                "baseToken": {"address": "0x456", "symbol": "OTHER"},
                "volume": {"h24": 1500},
            },
        ]

        result = adapter._deduplicate_pairs(pairs)

        assert len(result) == 2
        # Should keep first occurrence of duplicate
        assert result[0]["volume"]["h24"] == 1000
        assert result[1]["volume"]["h24"] == 1500

    def test_get_max_volume(self) -> None:
        """Test _get_max_volume calculates maximum volume."""
        adapter = DexScreenerAdapter()

        pairs = [
            {"volume": {"h24": 1000}},
            {"volume": {"h24": 2000}},
            {"volume": {"h24": 500}},
        ]

        result = adapter._get_max_volume(pairs)
        assert result == 2000

    def test_get_max_volume_empty(self) -> None:
        """Test _get_max_volume with empty pairs."""
        adapter = DexScreenerAdapter()

        result = adapter._get_max_volume([])
        assert result == 0

    def test_build_parent_dict(self) -> None:
        """Test _build_parent_dict creates correct parent structure."""
        adapter = DexScreenerAdapter()

        pair = {
            "baseToken": {
                "address": "0x123",
                "symbol": "TEST",
                "name": "Test Token",
            },
            "volume": {"h24": 1000},
            "pairUrl": "https://example.com/pair",
            "chainId": "ethereum",
            "dexId": "uniswap",
            "pairAddress": "0xpair",
        }

        result = adapter._build_parent_dict(pair, 2000)

        assert result["name"] == "Test Token"
        assert result["symbol"] == "TEST"
        assert result["score"] == 0.5  # 1000/2000
        assert result["source"] == "dexscreener"
        assert result["url"] == "https://example.com/pair"
        assert result["chain"] == "ethereum"
        assert result["address"] == "0x123"
        assert len(result["children"]) == 1

    def test_build_children(self) -> None:
        """Test _build_children creates correct children structure."""
        adapter = DexScreenerAdapter()

        pair = {
            "pairUrl": "https://example.com/pair",
            "chainId": "ethereum",
            "dexId": "uniswap",
            "pairAddress": "0xpair",
        }

        result = adapter._build_children(pair, 1000)

        assert len(result) == 1
        child = result[0]
        assert child["pair"] == "0xpair"
        assert child["chain"] == "ethereum"
        assert child["dex"] == "uniswap"
        assert child["url"] == "https://example.com/pair"
        assert child["vol24h"] == 1000

    def test_build_children_missing_data(self) -> None:
        """Test _build_children returns empty when data missing."""
        adapter = DexScreenerAdapter()

        pair = {"pairUrl": "", "chainId": ""}

        result = adapter._build_children(pair, 1000)

        assert not result

    def test_normalize_and_rank_empty(self) -> None:
        """Test _normalize_and_rank with empty pairs."""
        adapter = DexScreenerAdapter()

        result = adapter._normalize_and_rank([])
        assert not result

    def test_normalize_and_rank_sorts_by_score(self) -> None:
        """Test _normalize_and_rank sorts by score descending."""
        adapter = DexScreenerAdapter()

        pairs = [
            {"volume": {"h24": 1000}},
            {"volume": {"h24": 3000}},
            {"volume": {"h24": 2000}},
        ]

        with patch.object(adapter, "_build_parent_dict") as mock_build:
            mock_build.side_effect = [
                {"score": 0.33, "name": "Low"},
                {"score": 1.0, "name": "High"},
                {"score": 0.67, "name": "Medium"},
            ]

            result = adapter._normalize_and_rank(pairs)

            assert result[0]["name"] == "High"
            assert result[1]["name"] == "Medium"
            assert result[2]["name"] == "Low"

    def test_normalize_and_rank_caps_at_25(self) -> None:
        """Test _normalize_and_rank caps results at 25."""
        adapter = DexScreenerAdapter()

        # Create 30 pairs
        pairs = [{"volume": {"h24": 1000}}] * 30

        with patch.object(adapter, "_build_parent_dict") as mock_build:
            mock_build.return_value = {"score": 1.0, "name": "Test"}

            result = adapter._normalize_and_rank(pairs)

            assert len(result) == 25

    def test_fetch_parents_integration(self) -> None:
        """Test full fetch_parents integration."""
        adapter = DexScreenerAdapter()

        mock_pairs = [
            {
                "baseToken": {
                    "address": "0x123",
                    "symbol": "TEST",
                    "name": "Test Token",
                },
                "volume": {"h24": 1000},
                "pairUrl": "https://example.com/pair",
                "chainId": "ethereum",
                "dexId": "uniswap",
                "pairAddress": "0xpair",
            },
        ]

        with patch.object(adapter, "_query_dexscreener") as mock_query:
            mock_query.return_value = mock_pairs

            result = adapter.fetch_parents("test", ["WIF"])

            assert len(result) == 1
            parent = result[0]
            assert parent["name"] == "Test Token"
            assert parent["symbol"] == "TEST"
            assert parent["source"] == "dexscreener"
            assert parent["score"] == 1.0  # Only one parent, so max score
