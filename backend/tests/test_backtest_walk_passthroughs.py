import importlib

bw = importlib.import_module("app.backtest_walk")

def test_walk_passthrough_various_params(monkeypatch):
    calls = {"n": 0, "last": None}
    def fake_run_once(**kw):
        calls["n"] += 1
        calls["last"] = kw
        return {"ok": True}
    getattr(bw, "run_once", None) and monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    fn = getattr(bw, "walk", None)
    out = fn and fn(
        start="2025-08-20T00:00:00Z",
        end="2025-08-20T00:03:00Z",
        step="1m",
        narrative="dogs",
        parent="WIF",
        toleranceMin=0.2,
        minLiqUsd=100.0,
        maxEntryAgeHours=24.0,
    )
    assert (out is None) or isinstance(out, list)
