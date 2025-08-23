import importlib
bt = importlib.import_module("app.backtest")

def test_backtest_optional_helpers_tolerant(monkeypatch):
    # Light sample so run_once-like helpers (if present) have something to touch
    sample = [{"address": "A1", "tx5m": {"buys": 1, "sells": 0}}]
    monkeypatch.setattr(bt, "load_snapshot", lambda *a, **k: sample, raising=False)

    # Touch a couple of optional/private helpers if they exist
    h1 = getattr(bt, "_collect_metrics", None)
    h2 = getattr(bt, "_score_child", None)

    out1 = h1 and h1(sample)                # dict-like or None
    out2 = h2 and h2(sample[0])             # numeric/dict/None

    assert (out1 is None) or isinstance(out1, dict)
    assert (out2 is None) or isinstance(out2, (int, float, dict))
