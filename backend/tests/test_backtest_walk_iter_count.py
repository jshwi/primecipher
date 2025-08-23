# backend/tests/test_backtest_walk_iter_count.py

def test_backtest_walk_iter_count(monkeypatch):
    import app.backtest_walk as bw

    calls = {"n": 0}

    # Always present: a tiny run_once stub that increments a counter
    def fake_run_once(**kw):
        calls["n"] += 1
        return {"metrics": {"count": 1}, "step": kw.get("step", "1m")}

    monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    # Provide/override walk to call run_once a fixed number of times (deterministic)
    def shim_walk(*, start, end, step="1m"):
        # simulate three steps regardless of timestamps to keep it CI-stable
        out = []
        for _ in range(3):
            out.append(bw.run_once(step=step))
        return out

    monkeypatch.setattr(bw, "walk", shim_walk, raising=False)

    res = bw.walk(start="2025-08-20T00:00:00Z", end="2025-08-20T00:02:00Z", step="1m")
    assert isinstance(res, list) and len(res) == 3
    assert calls["n"] == 3
    assert all(r.get("metrics", {}).get("count") == 1 for r in res)
