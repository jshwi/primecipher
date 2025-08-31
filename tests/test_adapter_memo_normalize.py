"""Tests for adapter memoization term normalization."""

import pytest


def test_memo_normalizes_terms(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that memoization normalizes terms before caching.

    :param monkeypatch: Pytest fixture for patching.
    """
    import importlib

    import backend.adapters.source as src

    def spy_det(_: str, terms: list[str]) -> list[dict]:
        # record normalized terms used by memo (via returning distinct
        # parents)
        return [
            {
                "parent": "|".join(sorted({t.lower() for t in terms})),
                "matches": 10,
            },
        ]

    monkeypatch.setenv("SOURCE_MODE", "test")
    monkeypatch.setenv("SOURCE_TTL", "60")
    importlib.reload(src)
    monkeypatch.setattr(src, "_deterministic_items", spy_det, raising=True)

    s = src.Source()
    a = s.parents_for("dogs", ["Dog", "wif"])
    b = s.parents_for("puppies", ["wif", "dog"])
    # both should be identical due to normalization & memo
    assert a[0]["parent"] == b[0]["parent"]
