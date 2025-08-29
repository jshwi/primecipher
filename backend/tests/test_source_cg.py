import importlib
import httpx
import pytest


def reload_src(monkeypatch, ttl="60", mode="test", client_factory=None):
    monkeypatch.setenv("SOURCE_TTL", ttl)
    monkeypatch.setenv("SOURCE_MODE", mode)
    import app.adapters.source as src
    importlib.reload(src)
    src._raw_cache.clear()

    # If a fake client factory is passed, patch httpx.Client
    if client_factory:
        monkeypatch.setattr(httpx, "Client", client_factory)

    return src


class FakeResponse:
    def __init__(self, js):
        self._js = js

    def raise_for_status(self):
        return True

    def json(self):
        return self._js


class FakeClient:
    """Context manager wrapper for a fake get() function."""
    def __init__(self, get_func):
        self._get = get_func

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        return self._get(url, params or {})


def make_resp(js):
    return FakeResponse(js)


def test_cg_happy_path(monkeypatch):
    # normal case: coins returned
    def fake_get(url, params):
        return make_resp({"coins": [{"name": "Foxtrot", "market_cap_rank": 8}]})

    src = reload_src(monkeypatch, ttl="120",
                     mode="coingecko",
                     client_factory=lambda *a, **kw: FakeClient(fake_get))
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    assert isinstance(out, list)
    assert out[0]["parent"].lower() == "foxtrot"


def test_cg_empty_results(monkeypatch):
    # API returns no coins -> fallback to deterministic
    def fake_get(url, params):
        return make_resp({"coins": []})

    src = reload_src(monkeypatch, ttl="120",
                     mode="coingecko",
                     client_factory=lambda *a, **kw: FakeClient(fake_get))
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    assert isinstance(out, list)
    assert len(out) > 0


def test_cg_network_error_fallback(monkeypatch):
    # Simulate network failure by raising inside get()
    def fake_get(url, params):
        raise httpx.RequestError("boom", request=None)

    src = reload_src(monkeypatch, ttl="120",
                     mode="coingecko",
                     client_factory=lambda *a, **kw: FakeClient(fake_get))
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    # Should not raise; should fallback to deterministic
    assert isinstance(out, list)
    assert len(out) > 0
