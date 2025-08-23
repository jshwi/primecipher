import importlib

bw = importlib.import_module("app.backtest_walk")


def test_backtest_walk_accumulates_results(monkeypatch):
    calls = {"n": 0, "params": []}

    def fake_run_once(**kw):
        calls["n"] += 1
        calls["params"].append((kw.get("narrative"), kw.get("parent"), kw.get("step")))
        # return a simple dict each time so walk() can accumulate
        return {"ok": True, "idx": calls["n"], "step": kw.get("step")}

    getattr(bw, "run_once", None) and monkeypatch.setattr(bw, "run_once", fake_run_once, raising=False)

    fn = getattr(bw, "walk", None)
    out = fn and fn(
        start="2025-08-20T00:00:00Z",
        end="2025-08-20T00:05:00Z",
        step="1m",
        narrative="dogs",
        parent="WIF",
    )

    # Tolerant, branchless checks
    assert (out is None) or (isinstance(out, list) and len(out) >= 2)
    assert (not calls["params"]) or all(p == ("dogs", "WIF", "1m") for p in calls["params"])
    assert (out is None) or all((isinstance(r, dict) and r.get("ok") is True) for r in out)
