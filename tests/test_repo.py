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
    assert rows == sorted(items, key=lambda x: -x["matches"])


def test_replace_parents_overwrites_previous() -> None:
    """Test that replace_parents overwrites previous data."""
    narrative = list_narrative_names()[0]
    replace_parents(narrative, [{"parent": "old", "matches": 1}], time())
    replace_parents(narrative, [{"parent": "new", "matches": 9}], time())
    rows = list_parents(narrative)
    assert rows == [{"parent": "new", "matches": 9}]
