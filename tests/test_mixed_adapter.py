"""Tests for the mixed adapter."""

from unittest.mock import Mock, patch

from backend.adapters.mixed import MixedAdapter


class TestMixedAdapter:
    """Test cases for MixedAdapter."""

    def test_fetch_parents_empty_terms(self) -> None:
        """Test fetch_parents with empty terms returns empty list."""
        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", [])
        assert not result

    def test_fetch_parents_none_terms(self) -> None:
        """Test fetch_parents with None terms returns empty list."""
        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", None)  # type: ignore
        assert not result

    @patch("backend.adapters.mixed.CoinGeckoAdapter")
    @patch("backend.adapters.mixed.DexScreenerAdapter")
    def test_fetch_parents_success(
        self,
        mock_ds_adapter,
        mock_cg_adapter,
    ) -> None:
        """Test fetch_parents successfully merges data from both sources.

        :param mock_ds_adapter: Mocked DexScreener adapter.
        :param mock_cg_adapter: Mocked CoinGecko adapter.
        """
        # Mock CoinGecko data
        cg_data = [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "vol24h": 1000,
                "marketCap": 50000000000,
                "price": 50000,
                "url": "https://coingecko.com/bitcoin",
                "image": "btc.png",
                "address": "btc_address",
            },
        ]
        mock_cg_instance = Mock()
        mock_cg_instance.fetch_parents.return_value = cg_data
        mock_cg_adapter.return_value = mock_cg_instance

        # Mock DexScreener data
        ds_data = [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "vol24h": 800,
                "url": "https://dexscreener.com/btc",
                "chain": "ethereum",
                "address": "btc_address",
                "children": [{"pair": "btc_pair", "vol24h": 800}],
            },
        ]
        mock_ds_instance = Mock()
        mock_ds_instance.fetch_parents.return_value = ds_data
        mock_ds_adapter.return_value = mock_ds_instance

        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", ["bitcoin"])

        assert len(result) == 1
        item = result[0]
        assert item["name"] == "Bitcoin"
        assert item["symbol"] == "BTC"
        assert item["source"] == "coingecko+dexscreener"
        assert item["marketCap"] == 50000000000
        assert item["price"] == 50000
        assert item["image"] == "btc.png"
        assert item["chain"] == "ethereum"
        assert item["children"] == [{"pair": "btc_pair", "vol24h": 800}]
        assert "score" in item

    @patch("backend.adapters.mixed.CoinGeckoAdapter")
    @patch("backend.adapters.mixed.DexScreenerAdapter")
    def test_fetch_parents_only_cg_data(
        self,
        mock_ds_adapter,
        mock_cg_adapter,
    ) -> None:
        """Test fetch_parents with only CoinGecko data.

        :param mock_ds_adapter: Mocked DexScreener adapter.
        :param mock_cg_adapter: Mocked CoinGecko adapter.
        """
        cg_data = [
            {
                "name": "Ethereum",
                "symbol": "ETH",
                "vol24h": 2000,
                "marketCap": 200000000000,
                "price": 2000,
                "url": "https://coingecko.com/ethereum",
                "image": "eth.png",
                "address": "eth_address",
            },
        ]
        mock_cg_instance = Mock()
        mock_cg_instance.fetch_parents.return_value = cg_data
        mock_cg_adapter.return_value = mock_cg_instance

        mock_ds_instance = Mock()
        mock_ds_instance.fetch_parents.return_value = []
        mock_ds_adapter.return_value = mock_ds_instance

        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", ["ethereum"])

        assert len(result) == 1
        item = result[0]
        assert item["name"] == "Ethereum"
        assert item["symbol"] == "ETH"
        assert item["source"] == "coingecko"
        assert item["marketCap"] == 200000000000

    @patch("backend.adapters.mixed.CoinGeckoAdapter")
    @patch("backend.adapters.mixed.DexScreenerAdapter")
    def test_fetch_parents_only_ds_data(
        self,
        mock_ds_adapter,
        mock_cg_adapter,
    ) -> None:
        """Test fetch_parents with only DexScreener data.

        :param mock_ds_adapter: Mocked DexScreener adapter.
        :param mock_cg_adapter: Mocked CoinGecko adapter.
        """
        mock_cg_instance = Mock()
        mock_cg_instance.fetch_parents.return_value = []
        mock_cg_adapter.return_value = mock_cg_instance

        ds_data = [
            {
                "name": "Uniswap",
                "symbol": "UNI",
                "vol24h": 500,
                "url": "https://dexscreener.com/uni",
                "chain": "ethereum",
                "address": "uni_address",
                "children": [{"pair": "uni_pair", "vol24h": 500}],
            },
        ]
        mock_ds_instance = Mock()
        mock_ds_instance.fetch_parents.return_value = ds_data
        mock_ds_adapter.return_value = mock_ds_instance

        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", ["uniswap"])

        assert len(result) == 1
        item = result[0]
        assert item["name"] == "Uniswap"
        assert item["symbol"] == "UNI"
        assert item["source"] == "dexscreener"
        assert item["chain"] == "ethereum"

    @patch("backend.adapters.mixed.CoinGeckoAdapter")
    @patch("backend.adapters.mixed.DexScreenerAdapter")
    def test_fetch_parents_caps_at_25(
        self,
        mock_ds_adapter,
        mock_cg_adapter,
    ) -> None:
        """Test fetch_parents caps results at 25 items.

        :param mock_ds_adapter: Mocked DexScreener adapter.
        :param mock_cg_adapter: Mocked CoinGecko adapter.
        """
        # Create 30 items for each source
        cg_data = [
            {
                "name": f"Coin{i}",
                "symbol": f"COIN{i}",
                "vol24h": 100 + i,
                "marketCap": 1000000 + i,
                "price": 100 + i,
                "url": f"https://coingecko.com/coin{i}",
                "image": f"coin{i}.png",
                "address": f"coin{i}_address",
            }
            for i in range(30)
        ]
        mock_cg_instance = Mock()
        mock_cg_instance.fetch_parents.return_value = cg_data
        mock_cg_adapter.return_value = mock_cg_instance

        ds_data = [
            {
                "name": f"Token{i}",
                "symbol": f"TOKEN{i}",
                "vol24h": 50 + i,
                "url": f"https://dexscreener.com/token{i}",
                "chain": "ethereum",
                "address": f"token{i}_address",
                "children": [{"pair": f"token{i}_pair", "vol24h": 50 + i}],
            }
            for i in range(30)
        ]
        mock_ds_instance = Mock()
        mock_ds_instance.fetch_parents.return_value = ds_data
        mock_ds_adapter.return_value = mock_ds_instance

        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", ["crypto"])

        # Should cap at 25 items total
        assert len(result) <= 25

    def test_get_max_volume_from_data_empty(self) -> None:
        """Test _get_max_volume_from_data with empty data."""
        adapter = MixedAdapter()
        result = adapter._get_max_volume_from_data([], "vol24h")
        assert result == 0

    def test_get_max_volume_from_data_with_data(self) -> None:
        """Test _get_max_volume_from_data with data."""
        adapter = MixedAdapter()
        data = [
            {"vol24h": 100},
            {"vol24h": 200},
            {"vol24h": 150},
        ]
        result = adapter._get_max_volume_from_data(data, "vol24h")
        assert result == 200

    def test_renormalize_scores_empty(self) -> None:
        """Test _renormalize_scores with empty data."""
        adapter = MixedAdapter()
        result = adapter._renormalize_scores([])
        assert not result

    def test_renormalize_scores_zero_scores(self) -> None:
        """Test _renormalize_scores with zero scores."""
        adapter = MixedAdapter()
        data = [{"score": 0}, {"score": 0}]
        result = adapter._renormalize_scores(data)
        assert result == data

    def test_renormalize_scores_normalizes_and_sorts(self) -> None:
        """Test _renormalize_scores normalizes and sorts by score."""
        adapter = MixedAdapter()
        data = [
            {"score": 0.5, "name": "A"},
            {"score": 1.0, "name": "B"},
            {"score": 0.3, "name": "C"},
        ]
        result = adapter._renormalize_scores(data)

        # Should be sorted by score (descending)
        assert result[0]["name"] == "B"
        assert result[1]["name"] == "A"
        assert result[2]["name"] == "C"

        # Scores should be normalized (max should be 1.0)
        assert result[0]["score"] == 1.0
        assert result[1]["score"] == 0.5
        assert result[2]["score"] == 0.3

    @patch("backend.adapters.mixed.CoinGeckoAdapter")
    @patch("backend.adapters.mixed.DexScreenerAdapter")
    def test_fetch_parents_matches_by_address(
        self,
        mock_ds_adapter,
        mock_cg_adapter,
    ) -> None:
        """Test fetch_parents matches items by address when symbols differ.

        :param mock_ds_adapter: Mocked DexScreener adapter.
        :param mock_cg_adapter: Mocked CoinGecko adapter.
        """
        # Mock CoinGecko data with address
        cg_data = [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "vol24h": 1000,
                "marketCap": 50000000000,
                "price": 50000,
                "url": "https://coingecko.com/bitcoin",
                "image": "btc.png",
                "address": "0x1234567890abcdef",
            },
        ]
        mock_cg_instance = Mock()
        mock_cg_instance.fetch_parents.return_value = cg_data
        mock_cg_adapter.return_value = mock_cg_instance

        # Mock DexScreener data with same address but different symbol
        ds_data = [
            {
                "name": "Bitcoin Token",
                "symbol": "BTCTOKEN",  # Different symbol
                "vol24h": 800,
                "url": "https://dexscreener.com/btc",
                "chain": "ethereum",
                "address": "0x1234567890abcdef",  # Same address
                "children": [{"pair": "btc_pair", "vol24h": 800}],
            },
        ]
        mock_ds_instance = Mock()
        mock_ds_instance.fetch_parents.return_value = ds_data
        mock_ds_adapter.return_value = mock_ds_instance

        adapter = MixedAdapter()
        result = adapter.fetch_parents("test", ["bitcoin"])

        # Should have 1 merged item (the DexScreener item should be excluded)
        assert len(result) == 1
        item = result[0]
        assert item["name"] == "Bitcoin"  # Prefer CoinGecko name
        assert item["symbol"] == "BTC"  # Prefer CoinGecko symbol
        assert item["source"] == "coingecko+dexscreener"
        assert item["address"] == "0x1234567890abcdef"
        assert item["chain"] == "ethereum"  # Keep DexScreener chain
        assert item["children"] == [{"pair": "btc_pair", "vol24h": 800}]
