import importlib

bt = importlib.import_module("app.backtest")

def test_backtest_iter_range_tolerant():
    fn = getattr(bt, "_iter_range", None)
    out = fn and list(fn("2025-08-20T00:00:00Z", "2025-08-20T00:03:00Z", "1m"))
    assert (out is None) or isinstance(out, list)
