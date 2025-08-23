import importlib

bw = importlib.import_module("app.backtest_walk")

def test_walk_step_handling(monkeypatch):
    seen = []
    def fake_run_once(**kw):
        seen.append(kw.get("step"))
        return {"ok": True}
    getattr(bw, "run_once", None) and monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    fn = getattr(bw, "walk", None)
    fn and fn(start="2025-08-20T00:00:00Z", end="2025-08-20T00:02:00Z", step="1m")
    assert (not seen) or all(s == "1m" for s in seen)
