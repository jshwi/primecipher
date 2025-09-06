"""Tests for the blend adapter."""

# flake8: noqa: F841

from unittest.mock import MagicMock, patch

from backend.adapters.source import _make_blend


class TestBlendAdapter:
    """Test cases for the blend adapter."""

    def test_fetch_parents_empty_terms(self) -> None:
        """Test fetch_parents with empty terms."""
        adapter = _make_blend()
        result = adapter.fetch_parents("test_narrative_empty", [])
        assert not result

    def test_fetch_parents_none_terms(self) -> None:
        """Test fetch_parents with None terms."""
        adapter = _make_blend()
        result = adapter.fetch_parents("test_narrative_none", None)
        assert not result

    def test_fetch_parents_success_both_sources(self) -> None:
        """Test fetch_parents with both sources returning data."""
        adapter = _make_blend()

        # Mock data for both sources
        ds_items = [
            {"parent": "DS Token 1", "matches": 80, "source": "dexscreener"},
            {"parent": "DS Token 2", "matches": 60, "source": "dexscreener"},
        ]
        cg_items = [
            {"parent": "CG Token 1", "matches": 90, "source": "coingecko"},
            {"parent": "CG Token 2", "matches": 70, "source": "coingecko"},
        ]

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
            patch("backend.adapters.source._memo_raw") as mock_memo,
        ):

            # Mock the memo to return our test data
            mock_memo.return_value = ds_items + cg_items

            result = adapter.fetch_parents(
                "test_narrative_both",
                ["term1", "term2"],
            )

            # Should return concatenated lists
            assert len(result) == 4
            assert any(item["parent"] == "DS Token 1" for item in result)
            assert any(item["parent"] == "CG Token 1" for item in result)

            # Verify memo was called
            mock_memo.assert_called_once()

    def test_fetch_parents_only_dexscreener_success(self) -> None:
        """Test fetch_parents when only DexScreener succeeds."""
        adapter = _make_blend()

        ds_items = [
            {"parent": "DS Token 1", "matches": 80, "source": "dexscreener"},
        ]

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
            patch("backend.adapters.source._memo_raw") as mock_memo,
        ):

            # Mock the memo to return only DS items
            mock_memo.return_value = ds_items

            result = adapter.fetch_parents("test_narrative_ds_only", ["term1"])

            # Should return only DS items
            assert len(result) == 1
            assert result[0]["parent"] == "DS Token 1"

            # Verify memo was called
            mock_memo.assert_called_once()

    def test_fetch_parents_only_coingecko_success(self) -> None:
        """Test fetch_parents when only CoinGecko succeeds."""
        adapter = _make_blend()

        cg_items = [
            {"parent": "CG Token 1", "matches": 90, "source": "coingecko"},
        ]

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
            patch("backend.adapters.source._memo_raw") as mock_memo,
        ):

            # Mock the memo to return only CG items
            mock_memo.return_value = cg_items

            result = adapter.fetch_parents("test_narrative_cg_only", ["term1"])

            # Should return only CG items
            assert len(result) == 1
            assert result[0]["parent"] == "CG Token 1"

            # Verify memo was called
            mock_memo.assert_called_once()

    def test_fetch_parents_both_sources_fail(self) -> None:
        """Test fetch_parents when both sources fail."""
        adapter = _make_blend()

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
            patch("backend.adapters.source._memo_raw") as mock_memo,
        ):

            # Mock the memo to return empty list
            mock_memo.return_value = []

            result = adapter.fetch_parents("test_narrative_fail", ["term1"])

            # Should return empty list
            assert not result

            # Verify memo was called
            mock_memo.assert_called_once()

    def test_parents_for_with_parameters(self) -> None:
        """Test parents_for method with all parameters."""
        adapter = _make_blend()

        # Use parent names that contain the terms to pass require_all_terms
        ds_items = [
            {
                "parent": "term1 term2 DS Token",
                "matches": 80,
                "source": "dexscreener",
            },
        ]
        cg_items = [
            {
                "parent": "term1 term2 CG Token",
                "matches": 90,
                "source": "coingecko",
            },
        ]

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
            patch("backend.adapters.source._memo_raw") as mock_memo,
        ):

            # Mock the memo to return concatenated items
            mock_memo.return_value = ds_items + cg_items

            result = adapter.parents_for(
                "test_narrative_params",
                ["term1", "term2"],
                allow_name_match=False,
                block=["blocked"],
                require_all_terms=True,
            )

            # Should return concatenated lists
            assert len(result) == 2

            # Verify memo was called
            mock_memo.assert_called_once()

    def test_fetch_parents_exception_handling_coverage(self) -> None:
        """Test exception handling in the blend adapter for coverage."""
        adapter = _make_blend()

        with (
            patch(
                "backend.adapters.source.parents_for_dexscreener",
            ) as _mock_ds,  # pylint: disable=unused-variable
            patch(
                "backend.adapters.source._make_cg",
            ) as _mock_cg_factory,  # pylint: disable=unused-variable
        ):

            # Mock DS to raise an exception
            _mock_ds.side_effect = Exception("DS API error")

            # Mock CG to raise an exception
            mock_cg_adapter = MagicMock()
            mock_cg_adapter.parents_for.side_effect = Exception("CG API error")
            _mock_cg_factory.return_value = mock_cg_adapter

            result = adapter.fetch_parents(
                "test_narrative_exceptions",
                ["term1"],
            )

            # Should return empty list (both sources failed)
            assert not result

            # Verify both sources were called
            _mock_ds.assert_called_once_with(
                "test_narrative_exceptions",
                ["term1"],
            )
            mock_cg_adapter.parents_for.assert_called_once()

    def test_merge_parents_deduplication(self) -> None:
        """Test _merge_parents function with deduplication."""
        from backend.adapters.source import _merge_parents

        # Test data with overlapping items
        ds_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "chain": "ethereum",
                "address": "0x123",
                "price": 1.0,
                "vol24h": 1000,
                "liquidityUsd": 5000,
                "source": "dexscreener",
            },
            {
                "parent": "Token B",
                "symbol": "TOKENB",
                "chain": "ethereum",
                "address": "0x456",
                "price": 2.0,
                "vol24h": 2000,
                "liquidityUsd": 10000,
                "source": "dexscreener",
            },
        ]

        cg_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "chain": "ethereum",
                "address": "0x123",
                "price": 1.1,
                "vol24h": 1100,
                "marketCap": 1000000,
                "image": "https://example.com/token-a.png",
                "url": "https://coingecko.com/token-a",
                "source": "coingecko",
            },
            {
                "parent": "Token C",
                "symbol": "TOKENC",
                "chain": "ethereum",
                "address": "0x789",
                "price": 3.0,
                "vol24h": 3000,
                "marketCap": 2000000,
                "image": "https://example.com/token-c.png",
                "url": "https://coingecko.com/token-c",
                "source": "coingecko",
            },
        ]

        result = _merge_parents(ds_items, cg_items)

        # Should have 3 items (Token A merged, Token B from DS, Token C from CG)
        assert len(result) == 3

        # Find Token A (merged)
        token_a = next(item for item in result if item["parent"] == "Token A")
        assert token_a["price"] == 1.0  # DS price takes precedence
        assert token_a["vol24h"] == 1000  # DS vol24h takes precedence
        assert token_a["liquidityUsd"] == 5000  # DS only
        assert token_a["marketCap"] == 1000000  # CG only
        assert (
            token_a["image"] == "https://example.com/token-a.png"
        )  # CG preferred
        assert (
            token_a["url"] == "https://coingecko.com/token-a"
        )  # DS preferred
        assert token_a["source"] == "dexscreener,coingecko"
        assert token_a["sources"] == ["dexscreener", "coingecko"]

        # Find Token B (DS only)
        token_b = next(item for item in result if item["parent"] == "Token B")
        assert token_b["source"] == "dexscreener"
        assert "sources" not in token_b

        # Find Token C (CG only)
        token_c = next(item for item in result if item["parent"] == "Token C")
        assert token_c["source"] == "coingecko"
        assert "sources" not in token_c

    def test_merge_parents_fallback_deduplication(self) -> None:
        """Test _merge_parents function with fallback deduplication by symbol+name."""
        from backend.adapters.source import _merge_parents

        # Test data without chain/address but with symbol+name
        ds_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "price": 1.0,
                "vol24h": 1000,
                "source": "dexscreener",
            },
        ]

        cg_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "price": 1.1,
                "marketCap": 1000000,
                "source": "coingecko",
            },
        ]

        result = _merge_parents(ds_items, cg_items)

        # Should have 1 merged item
        assert len(result) == 1
        assert result[0]["parent"] == "Token A"
        assert result[0]["price"] == 1.0  # DS price takes precedence
        assert result[0]["marketCap"] == 1000000  # CG only
        assert result[0]["source"] == "dexscreener,coingecko"

    def test_merge_single_parent(self) -> None:
        """Test _merge_single_parent function."""
        from backend.adapters.source import _merge_single_parent

        ds_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "price": 1.0,
            "vol24h": 1000,
            "liquidityUsd": 5000,
            "url": "https://dexscreener.com/token-a",
            "source": "dexscreener",
        }

        cg_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "price": 1.1,
            "vol24h": 1100,
            "marketCap": 1000000,
            "image": "https://example.com/token-a.png",
            "url": "https://coingecko.com/token-a",
            "source": "coingecko",
        }

        result = _merge_single_parent(ds_item, cg_item)

        # Check field precedence
        assert result["price"] == 1.0  # DS if present
        assert result["vol24h"] == 1000  # DS if present
        assert result["liquidityUsd"] == 5000  # DS only
        assert result["marketCap"] == 1000000  # CG only
        assert (
            result["image"] == "https://example.com/token-a.png"
        )  # CG preferred
        assert (
            result["url"] == "https://dexscreener.com/token-a"
        )  # DS preferred
        assert result["source"] == "dexscreener,coingecko"
        assert result["sources"] == ["dexscreener", "coingecko"]

    def test_merge_single_parent_missing_fields(self) -> None:
        """Test _merge_single_parent function with missing fields."""
        from backend.adapters.source import _merge_single_parent

        ds_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "source": "dexscreener",
        }

        cg_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "price": 1.1,
            "vol24h": 1100,
            "marketCap": 1000000,
            "image": "https://example.com/token-a.png",
            "url": "https://coingecko.com/token-a",
            "source": "coingecko",
        }

        result = _merge_single_parent(ds_item, cg_item)

        # Check field precedence with missing DS fields
        assert result["price"] == 1.1  # CG when DS missing
        assert result["vol24h"] == 1100  # CG when DS missing
        assert result["marketCap"] == 1000000  # CG only
        assert (
            result["image"] == "https://example.com/token-a.png"
        )  # CG preferred
        assert (
            result["url"] == "https://coingecko.com/token-a"
        )  # CG when DS missing
        assert result["source"] == "dexscreener,coingecko"
        assert result["sources"] == ["dexscreener", "coingecko"]

    def test_merge_single_parent_source_precedence(self) -> None:
        """Test _merge_single_parent source field precedence."""
        from backend.adapters.source import _merge_single_parent

        # Test DS source only (CG has empty source field)
        ds_item = {"parent": "Token A", "source": "dexscreener"}
        cg_item = {"parent": "Token A", "source": ""}  # Empty source
        result = _merge_single_parent(ds_item, cg_item)
        assert result["source"] == "dexscreener"

        # Test CG source only (DS has empty source field)
        ds_item = {"parent": "Token A", "source": ""}  # Empty source
        cg_item = {"parent": "Token A", "source": "coingecko"}
        result = _merge_single_parent(ds_item, cg_item)
        assert result["source"] == "coingecko"

        # Test both sources present
        ds_item = {"parent": "Token A", "source": "dexscreener"}
        cg_item = {"parent": "Token A", "source": "coingecko"}
        result = _merge_single_parent(ds_item, cg_item)
        assert result["source"] == "dexscreener,coingecko"

    def test_merge_parents_fallback_key_only(self) -> None:
        """Test _merge_parents with items that only have fallback keys."""
        from backend.adapters.source import _merge_parents

        ds_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "name": "Token A",
                "price": 1.0,
                "vol24h": 1000.0,
                "source": "dexscreener",
            },
        ]
        cg_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "name": "Token A",
                "price": 2.0,
                "vol24h": 2000.0,
                "marketCap": 5000000.0,
                "source": "coingecko",
            },
        ]

        result = _merge_parents(ds_items, cg_items)

        assert len(result) == 1
        token_a = result[0]
        assert token_a["parent"] == "Token A"
        assert token_a["price"] == 1.0  # DS price preferred
        assert token_a["vol24h"] == 1000.0  # DS vol24h preferred
        assert token_a["marketCap"] == 5000000.0  # CG marketCap
        assert token_a["source"] == "dexscreener,coingecko"
        assert token_a["sources"] == ["dexscreener", "coingecko"]

    def test_merge_single_parent_extra_keys(self) -> None:
        """Test _merge_single_parent preserves extra keys from CG item."""
        from backend.adapters.source import _merge_single_parent

        ds_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "price": 1.0,
            "vol24h": 1000.0,
            "source": "dexscreener",
        }
        cg_item = {
            "parent": "Token A",
            "symbol": "TOKENA",
            "price": 2.0,
            "vol24h": 2000.0,
            "marketCap": 5000000.0,
            "extra_field1": "extra_value1",
            "extra_field2": "extra_value2",
            "source": "coingecko",
        }

        result = _merge_single_parent(ds_item, cg_item)

        # Extra fields should be preserved
        assert result["extra_field1"] == "extra_value1"
        assert result["extra_field2"] == "extra_value2"

    def test_merge_parents_no_primary_keys(self) -> None:
        """Test _merge_parents with items that have no primary keys (chain/address)."""
        from backend.adapters.source import _merge_parents

        # Items with only fallback keys (no chain/address)
        ds_items = [
            {
                "parent": "Token A",
                "symbol": "TOKENA",
                "name": "Token A",
                "price": 1.0,
                "vol24h": 1000.0,
                "source": "dexscreener",
            },
        ]
        cg_items = [
            {
                "parent": "Token B",
                "symbol": "TOKENB",
                "name": "Token B",
                "price": 2.0,
                "vol24h": 2000.0,
                "marketCap": 5000000.0,
                "source": "coingecko",
            },
        ]

        result = _merge_parents(ds_items, cg_items)

        # Should have 2 items since they have different fallback keys
        assert len(result) == 2
        # Should be sorted by matches, vol24h, marketCap, parent
        assert result[0]["parent"] == "Token B"  # Higher vol24h
        assert result[1]["parent"] == "Token A"
