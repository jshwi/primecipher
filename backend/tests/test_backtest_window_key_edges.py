import importlib

def test_backtest_window_key_edges():
    bt = importlib.import_module("app.backtest")

    # Known passthroughs
    assert bt._window_key("m5") == "m5"
    assert bt._window_key("h1") == "h1"
    assert bt._window_key("h6") == "h6"
    assert bt._window_key("h24") == "h24"

    # Odd string inputs should still return a string (stable key)
    for val in ["weird", "H24", "  h24  "]:
        out = bt._window_key(val)
        assert isinstance(out, str) and len(out) > 0
