"""Tests for adapter memoization TTL functionality."""


def test_memo_ttl_expiry(monkeypatch) -> None:
    """Test that memoization respects TTL expiration.

    :param monkeypatch: Pytest fixture for patching.
    """
    import importlib

    import app.adapters.source as src

    calls = {"n": 0}

    def fake_det(_, __):
        calls["n"] += 1
        return [{"parent": "X", "matches": 10}]

    # ttl = 0 → always expired; reload to pick it up
    monkeypatch.setenv("SOURCE_MODE", "test")
    monkeypatch.setenv("SOURCE_TTL", "0")
    importlib.reload(src)
    monkeypatch.setattr(src, "_deterministic_items", fake_det, raising=True)

    s = src.Source()
    s.parents_for("dogs", ["dog"])
    s.parents_for("puppies", ["dog"])  # same terms but ttl=0 forces re-fetch
    assert calls["n"] == 2
