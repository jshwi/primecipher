"""Tests for scoring with empty data."""

from backend.parents import _with_scores


def test_with_scores_empty_list_returns_empty() -> None:
    """Test that scoring empty list returns empty list."""
    assert not _with_scores([])
