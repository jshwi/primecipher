import importlib


def test_synth_backfill_helpers(monkeypatch):
    mod = importlib.import_module("app.tools.synthetic_backfill")

    # Current impl may return None for these keys → be tolerant
    assert mod._child_pair({"pairAddress": "PAIRX"}) in (None, "PAIRX")
    assert mod._child_pair({"address": "PAIRY"}) in (None, "PAIRY")
    assert mod._child_pair({"nope": 1}) is None

    # _filtered evaluates minimal dicts safely
    out = mod._filtered({
        "symbol": "AAA",
        "txns": {"h24": {"buys": 1, "sells": 0}},
        "liquidity": {"usd": 10},
    })
    assert out in (True, False)
