"""Tests for adapter memoization functionality."""

import importlib


def _fresh_src(monkeypatch, ttl="60", mode="test"):
    """Create a fresh source module with specified configuration."""
    monkeypatch.setenv("SOURCE_TTL", ttl)
    monkeypatch.setenv("SOURCE_MODE", mode)
    import backend.adapters.source as src

    importlib.reload(src)
    src._raw_cache.clear()
    return src


def test_memo_reuses_results(monkeypatch) -> None:
    """Test that memoization reuses results for same terms.

    :param monkeypatch: Pytest fixture for patching.
    """
    src = _fresh_src(monkeypatch, ttl="60", mode="test")

    calls = {"n": 0}

    def fake_det(_, __):
        calls["n"] += 1
        return [{"parent": "X", "matches": 10}]

    monkeypatch.setattr(src, "_deterministic_items", fake_det, raising=True)

    s = src.Source()
    s.parents_for("dogs", ["Dog", "wif"])
    s.parents_for("puppies", ["wif", "dog"])  # same terms, different narrative

    assert calls["n"] == 1  # second call hit memo


def test_memo_ttl_expired(monkeypatch) -> None:
    """Test that memoization expires after TTL.

    :param monkeypatch: Pytest fixture for patching.
    """
    src = _fresh_src(monkeypatch, ttl="10", mode="test")

    calls = {"n": 0}

    def fake_det(_, __):
        calls["n"] += 1
        return [{"parent": "X", "matches": 10}]

    monkeypatch.setattr(src, "_deterministic_items", fake_det, raising=True)

    # freeze time
    now = {"t": 1000.0}
    monkeypatch.setattr(src, "_now", lambda: now["t"], raising=True)

    s = src.Source()
    s.parents_for("dogs", ["dog"])  # caches at t=1000
    now["t"] = 1011.0  # advance beyond TTL=10
    s.parents_for("puppies", ["dog"])
    assert calls["n"] == 2  # cache miss due to expiry


def test_normalize_terms_equivalence(monkeypatch) -> None:
    """Test that term normalization produces equivalent results.

    :param monkeypatch: Pytest fixture for patching.
    """
    src = _fresh_src(monkeypatch)
    t1 = src._normalize_terms(["Dog", "wif"])
    t2 = src._normalize_terms(["wif", "dog", "Dog", "  "])
    assert t1 == t2
