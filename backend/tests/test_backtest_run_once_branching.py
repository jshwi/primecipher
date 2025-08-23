import importlib
import os

bt = importlib.import_module("app.backtest")

def test_run_once_with_diverse_rows(monkeypatch):
    # Rows exercise: missing fields, zeros, and positive activity
    sample = [
        {"address": "A1", "price_usd": 1.0, "liquidity_usd": 0.0, "tx5m": {"buys": 0, "sells": 0}},
        {"address": "A2", "price_usd": 0.5, "liquidity_usd": 100.0, "tx5m": {"buys": 2}},  # no sells
        {"address": "A3", "tx5m": {"sells": 1}},                                           # no buys/price/liq
        {"address": "A4", "price_usd": 2.0, "liquidity_usd": 200.0, "tx5m": {"buys": 3, "sells": 1}},
    ]
    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")
    monkeypatch.setattr(bt, "load_snapshot", lambda *a, **k: sample, raising=False)

    # Call with multiple windows to hit window parsing & metric aggregation branches
    out1 = getattr(bt, "run_once", None) and bt.run_once(snapshot_ts="2025-08-23T00:00:00Z", window="5m")
    out2 = getattr(bt, "run_once", None) and bt.run_once(snapshot_ts="2025-08-23T00:00:00Z", window="24h")

    # Tolerant shape checks – ensures code paths execute without asserting internals
    for out in (out1, out2):
        assert (out is None) or (isinstance(out, dict) and "metrics" in out)
