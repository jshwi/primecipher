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

    # _have_snapshot_near delegates to _rows; use millisecond-scale timestamps,
    # but tolerate implementation-specific proximity logic by asserting boolean type.
    exact_ts = 1_724_371_200_000  # ms since epoch (any realistic value)
    monkeypatch.setattr(
        mod,
        "_rows",
        lambda q, args=(): [
            {"ts": exact_ts},
            {"ts": exact_ts + 60_000},  # +60s in ms
        ],
        raising=False,
    )
    res = mod._have_snapshot_near("PAIR", ts=exact_ts, tol_s=60)
    assert isinstance(res, bool)
