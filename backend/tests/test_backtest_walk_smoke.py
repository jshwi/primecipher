def test_backtest_walk_smoke(monkeypatch):
    import app.backtest_walk as bw

    if not hasattr(bw, "walk"):
        import pytest
        pytest.skip("backtest_walk.walk not available in this build")

    calls = {"n": 0}

    def fake_run_once(**kw):
        calls["n"] += 1
        return {"metrics": {"count": 1}, "window": kw.get("step", "5m")}

    monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    out = bw.walk(
        start="2025-08-20T00:00:00Z",
        end="2025-08-20T00:02:00Z",
        step="1m",
    )
    results = list(out) if not isinstance(out, list) else out
    assert len(results) > 0
    assert calls["n"] >= 1
