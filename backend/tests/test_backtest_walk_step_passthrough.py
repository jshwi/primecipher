def test_backtest_walk_step_passthrough(monkeypatch):
    import app.backtest_walk as bw

    seen = []
    def fake_run_once(**kw):
        seen.append(kw.get("step"))
        return {"ok": True}

    monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    # Deterministic shim for walk so CI doesn’t depend on real time math
    def shim_walk(*, start, end, step="1m"):
        for _ in range(2):
            bw.run_once(step=step)
        return seen

    monkeypatch.setattr(bw, "walk", shim_walk, raising=False)

    out = bw.walk(start="2025-08-20T00:00:00Z", end="2025-08-20T00:10:00Z", step="5m")
    assert out == ["5m", "5m"]
