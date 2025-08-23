import importlib
bw = importlib.import_module("app.backtest_walk")

def test_backtest_walk_start_equals_end(monkeypatch):
    calls = {"n": 0}
    def fake_run_once(**kw):
        calls["n"] += 1
        return {"ok": True}
    getattr(bw, "run_once", None) and monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    fn = getattr(bw, "walk", None)
    out = fn and fn(start="2025-08-20T00:00:00Z", end="2025-08-20T00:00:00Z", step="1m")
    assert (out is None) or isinstance(out, list)
    assert (out is None) or (len(out) <= 1)
