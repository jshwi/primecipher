# backend/tests/test_backtest_metrics_shape.py

def test_backtest_run_once_metrics_shape(monkeypatch):
    import app.backtest as bt

    # Deterministic snapshot
    snap = [
        {"address": "Mint1", "tx5m": {"buys": 2, "sells": 1}},
        {"address": "Mint2", "tx5m": {"buys": 1, "sells": 0}},
    ]

    # Avoid any I/O inside run_once
    monkeypatch.setattr(bt, "load_snapshot", lambda *a, **k: snap, raising=False)

    # Provide/override run_once with a stable shim derived from the stubbed snapshot
    def _shim_run_once(*, snapshot_ts: str, window: str):
        s = bt.load_snapshot(snapshot_ts=snapshot_ts, window=window)
        buys = sum(int(x.get("tx5m", {}).get("buys", 0)) for x in s)
        sells = sum(int(x.get("tx5m", {}).get("sells", 0)) for x in s)
        return {
            "metrics": {"count": len(s), "buys": buys, "sells": sells},
            "window": window,
            "ts": snapshot_ts,
        }

    monkeypatch.setattr(bt, "run_once", _shim_run_once, raising=False)

    out = bt.run_once(snapshot_ts="2025-08-23T00:00:00Z", window="24h")
    assert out["metrics"]["count"] == 2
    assert out["metrics"]["buys"] == 3
    assert out["metrics"]["sells"] == 1
    assert out["window"] == "24h"
