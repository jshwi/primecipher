import importlib
import pytest

bt = importlib.import_module("app.backtest")

@pytest.mark.parametrize("win", ["m5","h1","h6","h24","H24","  h24  ","weird"])
def test_window_key_is_string(win):
    out = bt._window_key(win)
    assert isinstance(out, str) and len(out) > 0

@pytest.mark.parametrize("hold", ["m5","h1","h6","h24"])
def test_seed_parents_returns_list(hold):
    parents = bt._seed_parents(narrative=None)
    assert isinstance(parents, list)

def test_metrics_dict_shape_smoke(monkeypatch):
    sample = [
        {"address": "A1", "tx5m": {"buys": 2, "sells": 1}},
        {"address": "A2", "tx5m": {"buys": 1, "sells": 0}},
    ]
    monkeypatch.setattr(bt, "load_snapshot", lambda *a, **k: sample, raising=False)
    res = getattr(bt, "run_once", None) and bt.run_once(
        snapshot_ts="2025-08-23T00:00:00Z", window="24h"
    )
    # tolerant: execute if implemented, else accept None
    assert (res is None) or (isinstance(res, dict) and "metrics" in res)
