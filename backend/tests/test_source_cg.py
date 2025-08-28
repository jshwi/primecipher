import importlib
from types import SimpleNamespace
import time as _time
import pytest

def make_resp(payload, status_code=200):
    def _json():
        return payload
    def _raise():
        if status_code >= 400:
            raise Exception(f"http {status_code}")
    return SimpleNamespace(json=_json, raise_for_status=_raise)

class FakeClient:
    def __init__(self, get_fn):
        self._get = get_fn
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def get(self, url, params=None):
        return self._get(url, params or {})

def reload_src(monkeypatch, ttl="60", client_factory=None, patch_time=None):
    # ensure we aren't stuck in SOURCE_MODE=test from conftest
    monkeypatch.delenv("SOURCE_MODE", raising=False)
    monkeypatch.setenv("SOURCE_MODE", "coingecko")
    monkeypatch.setenv("SOURCE_TTL", ttl)

    import app.adapters.source as src_mod

    # patch httpx.Client BEFORE reload so the with-context is available
    if client_factory is not None:
        import httpx
        monkeypatch.setattr(httpx, "Client", client_factory)

    # clear cache and optionally patch time
    try:
        src_mod._cache.clear()
    except Exception:
        pass
    if patch_time is not None:
        monkeypatch.setattr(src_mod.time, "time", patch_time)

    # reload so env + patches are taken by module globals
    src_mod = importlib.reload(src_mod)
    # clear cache again now that we've reloaded
    src_mod._cache.clear()
    return src_mod

@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    # keep other tests clean
    monkeypatch.delenv("SOURCE_MODE", raising=False)
    monkeypatch.delenv("SOURCE_TTL", raising=False)

def test_cg_happy_path_top3_and_sorted(monkeypatch):
    coins = [
        {"name": "Alpha",  "market_cap_rank": 12},
        {"name": "Bravo",  "market_cap_rank": 5},
        {"name": "Delta",  "market_cap_rank": 9},
        {"name": "Charlie","market_cap_rank": 42},
    ]
    def fake_get(url, params):
        assert "search" in url
        assert params.get("query")
        return make_resp({"coins": coins})

    src = reload_src(monkeypatch, ttl="120",
                     client_factory=lambda timeout=...: FakeClient(fake_get))
    s = src.Source()
    out = s.parents_for("dogs", ["dog", "wif", "shib"])
    # Scores = 100 - rank → Bravo(95), Delta(91), Alpha(88) → top 3
    assert [o["parent"] for o in out] == ["Bravo", "Delta", "Alpha"]
    assert [o["matches"] for o in out] == sorted([o["matches"] for o in out], reverse=True)

def test_cg_cache_hit_skips_network(monkeypatch):
    calls = {"n": 0}
    def fake_get(url, params):
        calls["n"] += 1
        return make_resp({"coins": [{"name": "Echo", "market_cap_rank": 7}]})

    src = reload_src(monkeypatch, ttl="120",
                     client_factory=lambda timeout=...: FakeClient(fake_get))
    s = src.Source()
    terms = ["dog", "wif", "shib"]
    out1 = s.parents_for("dogs", terms)
    out2 = s.parents_for("dogs", terms)  # served from cache
    assert calls["n"] == 1
    assert out1 == out2
    assert len(out1) == 1 if len(out1) < 3 else 3  # adapter truncates to 3 if >3

def test_cg_cache_ttl_expiry(monkeypatch):
    # TTL=1s, advance time between calls to force miss
    now = [_time.time()]
    def fake_time():
        return now[0]

    calls = {"i": 0}
    def fake_get(url, params):
        calls["i"] += 1
        if calls["i"] == 1:
            return make_resp({"coins": [{"name": "Foxtrot", "market_cap_rank": 8}]})
        else:
            return make_resp({"coins": [{"name": "Golf", "market_cap_rank": 6}]})

    src = reload_src(
        monkeypatch,
        ttl="1",
        client_factory=lambda timeout=...: FakeClient(fake_get),
        patch_time=fake_time,
    )
    s = src.Source()
    terms = ["dog"]

    out1 = s.parents_for("dogs", terms)   # fills cache (Foxtrot)
    out2 = s.parents_for("dogs", terms)   # within TTL → cache hit
    assert [o["parent"] for o in out1] == [o["parent"] for o in out2]

    # advance beyond TTL → cache miss → new result (Golf)
    now[0] += 2.5
    out3 = s.parents_for("dogs", terms)
    assert [o["parent"] for o in out3] != [o["parent"] for o in out1]

def test_cg_empty_results_fallback_to_deterministic(monkeypatch):
    def fake_get(url, params):
        return make_resp({"coins": []})  # no results

    src = reload_src(monkeypatch, ttl="120",
                     client_factory=lambda timeout=...: FakeClient(fake_get))
    s = src.Source()
    out = s.parents_for("dogs", ["dog"])
    assert len(out) == 3
    assert sorted([x["matches"] for x in out], reverse=True) == [11, 10, 9]

def test_cg_network_error_fallback(monkeypatch):
    def fake_get(url, params):
        raise RuntimeError("network down")

    src = reload_src(monkeypatch, ttl="120",
                     client_factory=lambda timeout=...: FakeClient(fake_get))
    s = src.Source()
    out = s.parents_for("dogs", ["dog"])
    assert len(out) == 3
    assert sorted([x["matches"] for x in out], reverse=True) == [11, 10, 9]
