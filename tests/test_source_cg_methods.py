"""Tests for CoinGecko adapter methods in source.py."""

# pylint: disable=attribute-defined-outside-init,too-many-lines

from unittest.mock import MagicMock, patch

from backend.adapters.source import _make_cg


# pylint: disable=too-many-public-methods
class TestCGAdapterMethods:
    """Test individual methods of the CoinGecko adapter.

    Args:
        _mock_sleep: Mock for time.sleep function
        mock_client: Mock for httpx.Client
    """

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.adapter = _make_cg()  # type: ignore

    @patch("backend.adapters.source._get_json")
    @patch("time.sleep")
    def test_search_coins_success(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _search_coins with successful API response.

        Args:
            _mock_sleep: Mock for time.sleep function
            mock_get_json: Mock for _get_json function
        """
        # Mock response
        mock_get_json.return_value = {
            "coins": [
                {"name": "Bitcoin", "id": "bitcoin", "market_cap_rank": 1},
                {"name": "Ethereum", "id": "ethereum", "market_cap_rank": 2},
            ],
        }

        # Test the method
        coin_ids = self.adapter._search_coins(["bitcoin"])

        # Assertions
        assert len(coin_ids) == 2
        assert "bitcoin" in coin_ids
        assert "ethereum" in coin_ids

        # Verify API call was made
        mock_get_json.assert_called_once()
        _mock_sleep.assert_called_once_with(0.25)

    @patch("backend.adapters.source._get_json")
    @patch("time.sleep")
    def test_search_coins_api_error(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _search_coins handles API errors gracefully.

        Args:
            _mock_sleep: Mock for time.sleep function
            mock_get_json: Mock for _get_json function
        """
        # Mock API error
        mock_get_json.return_value = None

        coin_ids = self.adapter._search_coins(["bitcoin"])

        assert len(coin_ids) == 0  # No IDs collected

    @patch("backend.adapters.source._get_json")
    @patch("time.sleep")
    def test_get_market_data_success(
        self,
        mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test _get_market_data with successful API response.

        Args:
            mock_sleep: Mock for time.sleep function
            mock_get_json: Mock for _get_json function
        """
        # Mock market data response
        mock_get_json.return_value = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "current_price": 45000,
                "market_cap": 800000000000,
                "total_volume": 1000000000,
                "image": "https://example.com/btc.png",
            },
        ]

        # Test the method
        result = self.adapter._get_market_data(["bitcoin"])

        # Assertions
        assert len(result) == 1
        assert result[0]["id"] == "bitcoin"
        assert result[0]["name"] == "Bitcoin"

        # Verify API call was made
        mock_get_json.assert_called_once()
        mock_sleep.assert_called_once_with(0.25)

    def test_get_market_data_empty_ids(self) -> None:
        """Test _get_market_data with empty coin IDs list."""
        result = self.adapter._get_market_data([])
        assert not result

    def test_map_market_to_items(self) -> None:
        """Test _map_market_to_items method."""
        market_data = [
            {
                "name": "Bitcoin",
                "symbol": "btc",
                "id": "bitcoin",
                "total_volume": 1000000000,
                "market_cap": 800000000000,
                "current_price": 45000,
                "image": "https://example.com/btc.png",
            },
            {
                "name": "Ethereum",
                "symbol": "eth",
                "id": "ethereum",
                "total_volume": 500000000,
                "market_cap": 400000000000,
                "current_price": 3000,
                "image": "https://example.com/eth.png",
            },
        ]

        result = self.adapter._map_market_to_items(market_data)

        assert len(result) == 2

        # Check first item (Bitcoin should be first due to higher volume)
        btc_item = result[0]
        assert btc_item["parent"] == "Bitcoin"
        assert btc_item["symbol"] == "BTC"
        assert btc_item["price"] == 45000
        assert btc_item["marketCap"] == 800000000000
        assert btc_item["vol24h"] == 1000000000
        assert btc_item["matches"] == 100  # Highest volume
        assert btc_item["source"] == "coingecko"
        assert btc_item["url"] == "https://www.coingecko.com/en/coins/bitcoin"

        # Check second item (Ethereum)
        eth_item = result[1]
        assert eth_item["parent"] == "Ethereum"
        assert eth_item["symbol"] == "ETH"
        assert eth_item["price"] == 3000
        assert eth_item["marketCap"] == 400000000000
        assert eth_item["vol24h"] == 500000000
        assert eth_item["matches"] == 50  # Half of Bitcoin's volume
        assert eth_item["source"] == "coingecko"
        assert eth_item["url"] == "https://www.coingecko.com/en/coins/ethereum"

    def test_map_market_to_items_no_volume_fallback(self) -> None:
        """Test _map_market_to_items fallback when no volume data."""
        market_data = [
            {
                "name": "Bitcoin",
                "symbol": "btc",
                "id": "bitcoin",
                "total_volume": 0,
                "market_cap": 800000000000,
                "current_price": 45000,
                "image": "https://example.com/btc.png",
            },
        ]

        result = self.adapter._map_market_to_items(market_data)

        assert len(result) == 1
        assert result[0]["matches"] == 10  # Fallback value

    def test_map_market_to_items_filters_empty_names(self) -> None:
        """Test _map_market_to_items filters out items with empty names."""
        market_data = [
            {
                "name": "",
                "symbol": "btc",
                "id": "bitcoin",
                "total_volume": 1000000000,
                "market_cap": 800000000000,
                "current_price": 45000,
            },
            {
                "name": "Bitcoin",
                "symbol": "btc",
                "id": "bitcoin2",
                "total_volume": 500000000,
                "market_cap": 400000000000,
                "current_price": 3000,
            },
        ]

        result = self.adapter._map_market_to_items(market_data)

        # Should only return the item with a valid name
        assert len(result) == 1
        assert result[0]["parent"] == "Bitcoin"

    def test_filter_terms(self) -> None:
        """Test _filter_terms method."""
        # Test normal filtering
        terms = ["bitcoin", "ethereum", "dogecoin", "swap", "defi"]
        result = self.adapter._filter_terms(terms)
        assert result == ["bitcoin", "ethereum", "dogecoin"]

        # Test empty terms
        result = self.adapter._filter_terms([])
        assert not result

        # Test short terms
        terms = ["bt", "eth", "bitcoin"]
        result = self.adapter._filter_terms(terms)
        assert result == ["eth", "bitcoin"]

        # Test generic terms
        terms = ["bitcoin", "swap", "defi"]
        result = self.adapter._filter_terms(terms)
        assert result == ["bitcoin"]

    @patch("backend.adapters.source._get_json")
    @patch("time.sleep")
    def test_parents_for_success(
        self,
        _mock_sleep: MagicMock,
        mock_get_json: MagicMock,
    ) -> None:
        """Test parents_for with successful API responses.

        Args:
            _mock_sleep: Mock for time.sleep function
            mock_get_json: Mock for _get_json function
        """
        # Mock search response
        search_response = {
            "coins": [
                {"name": "Bitcoin", "id": "bitcoin", "market_cap_rank": 1},
            ],
        }

        # Mock market data response
        market_response = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "current_price": 45000,
                "market_cap": 800000000000,
                "total_volume": 1000000000,
                "image": "https://example.com/btc.png",
            },
        ]

        # Set up the mock to return different responses for different calls
        mock_get_json.side_effect = [
            search_response,  # Call in _search_coins
            market_response,  # Call in _get_market_data
        ]

        result = self.adapter.parents_for("test", ["bitcoin"])

        # Should return the mapped market data
        assert len(result) == 1
        assert result[0]["parent"] == "Bitcoin"
        assert result[0]["symbol"] == "BTC"
        assert result[0]["source"] == "coingecko"

    def test_parents_for_no_terms(self) -> None:
        """Test parents_for with no valid terms."""
        result = self.adapter.parents_for("test", [])
        assert not result

    def test_parents_for_filtered_terms(self) -> None:
        """Test parents_for with terms that get filtered out."""
        result = self.adapter.parents_for("test", ["swap", "defi", "bt"])
        assert not result
