"""Tests for repository operations."""

import typing as t
from time import time

from backend.repo import list_parents, replace_parents
from backend.seeds import list_narrative_names


def test_replace_and_list_parents_roundtrip() -> None:
    """Test that replace and list parents work together correctly."""
    narrative = list_narrative_names()[0]  # e.g. 'dogs'
    items: list[dict[str, t.Any]] = [
        {"parent": "p1", "matches": 5},
        {"parent": "p2", "matches": 7},
    ]
    ts = time()
    replace_parents(narrative, items, ts)

    rows = list_parents(narrative)
    expected = [
        {
            "parent": item["parent"],
            "matches": item["matches"],
            "symbol": None,
            "source": None,
            "price": None,
            "marketCap": None,
            "vol24h": None,
            "liquidityUsd": None,
            "chain": None,
            "address": None,
            "url": None,
            "image": None,
        }
        for item in sorted(items, key=lambda x: -x["matches"])
    ]
    assert rows == expected


def test_replace_parents_overwrites_previous() -> None:
    """Test that replace_parents overwrites previous data."""
    narrative = list_narrative_names()[0]
    replace_parents(narrative, [{"parent": "old", "matches": 1}], time())
    replace_parents(narrative, [{"parent": "new", "matches": 9}], time())
    rows = list_parents(narrative)
    expected = [
        {
            "parent": "new",
            "matches": 9,
            "symbol": None,
            "source": None,
            "price": None,
            "marketCap": None,
            "vol24h": None,
            "liquidityUsd": None,
            "chain": None,
            "address": None,
            "url": None,
            "image": None,
        },
    ]
    assert rows == expected


def test_replace_parents_deduplicates_duplicates() -> None:
    """Test that replace_parents deduplicates duplicate parents."""
    narrative = list_narrative_names()[0]
    # Create items with duplicates (case insensitive)
    items: list[dict[str, t.Any]] = [
        {"parent": "DOGE", "matches": 5},
        {"parent": "doge", "matches": 7},  # duplicate (case insensitive)
        {"parent": "BTC", "matches": 3},
        {"parent": "btc", "matches": 8},  # duplicate (case insensitive)
        {"parent": "ETH", "matches": 2},
    ]
    ts = time()
    replace_parents(narrative, items, ts)

    rows = list_parents(narrative)
    # Should only have 3 unique parents (DOGE, BTC, ETH)
    # First occurrence kept (DOGE with matches=5, BTC with matches=3)
    # Results are ordered by matches descending
    expected = [
        {
            "parent": "DOGE",
            "matches": 5,
            "symbol": None,
            "source": None,
            "price": None,
            "marketCap": None,
            "vol24h": None,
            "liquidityUsd": None,
            "chain": None,
            "address": None,
            "url": None,
            "image": None,
        },
        {
            "parent": "BTC",
            "matches": 3,
            "symbol": None,
            "source": None,
            "price": None,
            "marketCap": None,
            "vol24h": None,
            "liquidityUsd": None,
            "chain": None,
            "address": None,
            "url": None,
            "image": None,
        },
        {
            "parent": "ETH",
            "matches": 2,
            "symbol": None,
            "source": None,
            "price": None,
            "marketCap": None,
            "vol24h": None,
            "liquidityUsd": None,
            "chain": None,
            "address": None,
            "url": None,
            "image": None,
        },
    ]
    assert len(rows) == 3
    assert rows == expected
