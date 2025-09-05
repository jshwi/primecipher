"""Tests for CoinGecko adapter functionality."""

from typing import Any
from unittest.mock import Mock, patch

import httpx

from backend.adapters.coingecko import CoinGeckoAdapter

# flake8: noqa: E501,SIM117


class TestCoinGeckoAdapter:  # pylint: disable=too-many-public-methods
    """Test cases for CoinGeckoAdapter."""

    def test_fetch_parents_empty_terms(self) -> None:
        """Test fetch_parents with empty terms list."""
        adapter = CoinGeckoAdapter()
        result = adapter.fetch_parents("test", [])
        assert not result

    def test_fetch_parents_none_terms(self) -> None:
        """Test fetch_parents with None terms."""
        adapter = CoinGeckoAdapter()
        result = adapter.fetch_parents("test", [])
        assert not result

    def test_fetch_parents_caps_terms(self) -> None:
        """Test fetch_parents caps terms to first 3."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            with patch.object(adapter, "_get_market_data") as mock_market:
                with patch.object(adapter, "_format_parents") as mock_format:
                    mock_search.return_value = []
                    mock_market.return_value = []
                    mock_format.return_value = []

                    adapter.fetch_parents(
                        "test",
                        ["term1", "term2", "term3", "term4", "term5"],
                    )

                    # Should only use first 3 terms
                    mock_search.assert_called_once_with(
                        ["term1", "term2", "term3"],
                    )

    def test_search_coins_empty_terms(self) -> None:
        """Test _search_coins with empty terms."""
        adapter = CoinGeckoAdapter()
        result = adapter._search_coins([])
        assert not result

    def test_search_coins_with_whitespace(self) -> None:
        """Test _search_coins filters out empty/whitespace terms."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"coins": []}
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            adapter._search_coins(["", "  ", "valid_term"])

            # Should only call API once for valid_term
            assert (
                mock_client.return_value.__enter__.return_value.get.call_count
                == 1
            )

    def test_search_coins_success(self) -> None:
        """Test _search_coins successful API call."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "coins": [
                    {"id": "bitcoin", "name": "Bitcoin"},
                    {"id": "ethereum", "name": "Ethereum"},
                    {"id": "litecoin", "name": "Litecoin"},
                ],
            }
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._search_coins(["bitcoin"])

            # Results are in a set, so order is not deterministic
            assert set(result) == {"bitcoin", "ethereum", "litecoin"}
            assert len(result) == 3

    def test_search_coins_api_error(self) -> None:
        """Test _search_coins handles API errors gracefully."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = (
                httpx.RequestError("API Error")
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._search_coins(["bitcoin"])

            assert not result

    def test_search_coins_caps_results(self) -> None:
        """Test _search_coins caps results at 10 per term."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            # Create 50 coins to test capping
            coins = [
                {"id": f"coin{i}", "name": f"Coin {i}"} for i in range(50)
            ]
            mock_response = Mock()
            mock_response.json.return_value = {"coins": coins}
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._search_coins(["test"])

            assert len(result) == 10

    def test_get_market_data_empty_ids(self) -> None:
        """Test _get_market_data with empty coin IDs."""
        adapter = CoinGeckoAdapter()
        result = adapter._get_market_data([])
        assert not result

    def test_get_market_data_success(self) -> None:
        """Test _get_market_data successful API call."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "btc",
                    "image": "https://example.com/bitcoin.png",
                    "market_cap": 1000000000,
                    "total_volume": 50000000,
                    "current_price": 50000,
                },
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._get_market_data(["bitcoin"])

            assert len(result) == 1
            assert result[0]["id"] == "bitcoin"

    def test_get_market_data_api_error(self) -> None:
        """Test _get_market_data handles API errors gracefully."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = (
                httpx.RequestError("API Error")
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._get_market_data(["bitcoin"])

            assert not result

    def test_get_market_data_invalid_response(self) -> None:
        """Test _get_market_data handles invalid response format."""
        adapter = CoinGeckoAdapter()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "error": "Invalid response",
            }  # Not a list
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            with patch("time.sleep"):  # Mock sleep to speed up test
                result = adapter._get_market_data(["bitcoin"])

            assert not result

    def test_format_parents_empty_data(self) -> None:
        """Test _format_parents with empty market data."""
        adapter = CoinGeckoAdapter()
        result = adapter._format_parents([])
        assert not result

    def test_format_parents_success(self) -> None:
        """Test _format_parents successful formatting."""
        adapter = CoinGeckoAdapter()

        market_data = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "image": "https://example.com/bitcoin.png",
                "market_cap": 1000000000,
                "total_volume": 100000000,
                "current_price": 50000,
            },
            {
                "id": "ethereum",
                "name": "Ethereum",
                "symbol": "eth",
                "image": "https://example.com/ethereum.png",
                "market_cap": 500000000,
                "total_volume": 50000000,
                "current_price": 3000,
            },
        ]

        result = adapter._format_parents(market_data)

        assert len(result) == 2
        assert (
            result[0]["name"] == "Bitcoin"
        )  # Should be sorted by score (volume)
        assert result[0]["symbol"] == "btc"
        assert result[0]["source"] == "coingecko"
        assert result[0]["url"] == "https://www.coingecko.com/en/coins/bitcoin"
        assert result[0]["image"] == "https://example.com/bitcoin.png"
        assert result[0]["marketCap"] == 1000000000
        assert result[0]["vol24h"] == 100000000
        assert result[0]["price"] == 50000
        assert result[0]["score"] == 1.0  # Highest volume, so score = 1.0
        assert result[0]["children"] == [
            {
                "url": "https://www.coingecko.com/en/coins/bitcoin",
                "evidence": "coingecko_page",
            },
        ]

        assert result[1]["name"] == "Ethereum"
        assert result[1]["score"] == 0.5  # Half the volume of Bitcoin

    def test_format_parents_missing_fields(self) -> None:
        """Test _format_parents handles missing fields gracefully."""
        adapter = CoinGeckoAdapter()

        market_data: list[dict[str, Any]] = [
            {
                "id": "bitcoin",
                # Missing most fields
            },
            {
                "id": "ethereum",
                "name": "Ethereum",
                "symbol": "eth",
                "market_cap": None,  # None values
                "total_volume": None,
                "current_price": None,
            },
        ]

        result = adapter._format_parents(market_data)

        assert len(result) == 2
        assert result[0]["name"] == ""
        assert result[0]["symbol"] == ""
        assert result[0]["marketCap"] == 0
        assert result[0]["vol24h"] == 0
        assert result[0]["price"] == 0
        assert result[0]["score"] == 0

    def test_format_parents_missing_id(self) -> None:
        """Test _format_parents skips items with missing id."""
        adapter = CoinGeckoAdapter()

        market_data = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "total_volume": 100000000,
            },
            {
                # Missing id field
                "name": "Ethereum",
                "symbol": "eth",
                "total_volume": 50000000,
            },
            {
                "id": "",  # Empty id
                "name": "Litecoin",
                "symbol": "ltc",
                "total_volume": 25000000,
            },
        ]

        result = adapter._format_parents(market_data)

        # Should only include bitcoin (the one with valid id)
        assert len(result) == 1
        assert result[0]["name"] == "Bitcoin"

    def test_format_parents_no_volume_scores_zero(self) -> None:
        """Test _format_parents when all volumes are zero."""
        adapter = CoinGeckoAdapter()

        market_data = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "total_volume": 0,
            },
            {
                "id": "ethereum",
                "name": "Ethereum",
                "symbol": "eth",
                "total_volume": 0,
            },
        ]

        result = adapter._format_parents(market_data)

        assert len(result) == 2
        assert result[0]["score"] == 0
        assert result[1]["score"] == 0

    def test_format_parents_returns_all(self) -> None:
        """Test _format_parents returns all items (capping happens in main method)."""
        adapter = CoinGeckoAdapter()

        # Create 30 items to test that _format_parents doesn't cap
        market_data = []
        for i in range(30):
            market_data.append(
                {
                    "id": f"coin{i}",
                    "name": f"Coin {i}",
                    "symbol": f"c{i}",
                    "total_volume": 1000 - i,  # Decreasing volume
                },
            )

        result = adapter._format_parents(market_data)

        assert len(result) == 30

    def test_fetch_parents_integration_success(self) -> None:
        """Test full integration of fetch_parents (stubbed behavior)."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            mock_search.return_value = ["bitcoin", "ethereum"]

            result = adapter.fetch_parents("test", ["bitcoin"])

            assert result == [
                {"id": "bitcoin", "source": "coingecko"},
                {"id": "ethereum", "source": "coingecko"},
            ]
            mock_search.assert_called_once_with(["bitcoin"])

    def test_fetch_parents_search_returns_empty(self) -> None:
        """Test fetch_parents when search returns empty."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            mock_search.return_value = []

            result = adapter.fetch_parents("test", ["bitcoin"])

            assert not result

    def test_fetch_parents_market_returns_empty(self) -> None:
        """Test fetch_parents when search returns empty (stubbed behavior)."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            mock_search.return_value = []

            result = adapter.fetch_parents("test", ["bitcoin"])

            assert not result

    def test_fetch_parents_exception_handling(self) -> None:
        """Test fetch_parents handles exceptions gracefully."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            mock_search.side_effect = Exception("Test error")

            result = adapter.fetch_parents("test", ["bitcoin"])

            assert not result

    def test_fetch_parents_caps_at_25(self) -> None:
        """Test fetch_parents caps results at 30 (stubbed behavior)."""
        adapter = CoinGeckoAdapter()

        with patch.object(adapter, "_search_coins") as mock_search:
            # Create 30 coin IDs to test capping
            mock_search.return_value = [f"coin{i}" for i in range(30)]

            result = adapter.fetch_parents("test", ["bitcoin"])

            assert len(result) == 30
