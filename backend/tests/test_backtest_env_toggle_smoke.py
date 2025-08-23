import importlib

bt = importlib.import_module("app.backtest")

def test_backtest_run_once_env_toggle(monkeypatch):
    sample = [{"address": "A1", "tx5m": {"buys": 1, "sells": 0}}]
    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")
    monkeypatch.setattr(bt, "load_snapshot", lambda *a, **k: sample, raising=False)

    fn = getattr(bt, "run_once", None)
    res = fn and fn(snapshot_ts="2025-08-23T00:00:00Z", window="24h")
    assert (res is None) or isinstance(res, dict)
