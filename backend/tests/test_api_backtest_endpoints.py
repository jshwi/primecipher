import importlib
from fastapi.testclient import TestClient

main = importlib.import_module("app.main")


def test_backtest_and_walk_endpoints(monkeypatch):
    bt = importlib.import_module("app.backtest")
    bw = importlib.import_module("app.backtest_walk")
    dbg = importlib.import_module("app.debug")

    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")

    # monkeypatch core calls, but accept that routers may have bound originals
    monkeypatch.setattr(
        bt,
        "run_once",
        lambda **kw: {"ok": True, "echo": kw},
        raising=False,
    )
    monkeypatch.setattr(
        bw,
        "walk",
        lambda **kw: {"diagnostics": {"echo": kw}, "results": [{"ok": True}]},
        raising=False,
    )

    class _FakeAdapter:
        def fetch_children_for_parent(self, **kw):
            return [{"symbol": "CHILD", "address": "MintX"}]

    monkeypatch.setattr(
        dbg, "make_onchain_adapter", lambda *_a, **_k: _FakeAdapter(), raising=False
    )

    client = TestClient(main.app)

    # /backtest should return a dict with params/summary/results keys
    r1 = client.get("/backtest?narrative=dogs&parent=WIF&hold=h6&liqMinUsd=50000")
    assert r1.status_code == 200
    j1 = r1.json()
    assert isinstance(j1, dict)
    assert "params" in j1 and "summary" in j1
    if "results" in j1:
        assert isinstance(j1["results"], list)

    # /backtest/walk should return a dict with some list payload
    r2 = client.get(
        "/backtest/walk?narrative=dogs&parent=WIF&hold=h6&minLiqUsd=50000&toleranceMin=20"
    )
    assert r2.status_code == 200
    j2 = r2.json()
    assert isinstance(j2, dict)
    assert any(isinstance(v, list) for v in j2.values())

    # /debug/children should return dict with children list
    r3 = client.get("/debug/children/WIF?narrative=dogs&applyBlocklist=true&limit=5")
    assert r3.status_code == 200
    j3 = r3.json()
    assert isinstance(j3, dict)
    assert "children" in j3 and isinstance(j3["children"], list)
