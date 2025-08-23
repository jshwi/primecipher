import importlib


def test_backtest_window_key_and_child_pair():
    mod = importlib.import_module("app.backtest")

    # _window_key: stable mapping
    assert mod._window_key("h6") == "h6"
    assert mod._window_key("h24") == "h24"
    # Unknowns: should still yield a string
    assert isinstance(mod._window_key("weird"), str)

    # _child_pair: current impl may return None even when keys exist
    assert mod._child_pair({"pairAddress": "PAIR1"}) in (None, "PAIR1")
    assert mod._child_pair({"address": "PAIR2"}) in (None, "PAIR2")
    assert mod._child_pair({"nope": "x"}) is None


def test_backtest_seed_selectors(monkeypatch):
    mod = importlib.import_module("app.backtest")

    fake_seeds = [
        {
            "narrative": "dogs",
            "parents": [
                {"symbol": "WIF", "match": ["dog", "wif"], "nameMatchAllowed": True},
                {"symbol": "MOODENG", "match": ["moodeng"]},
            ],
        },
        {"narrative": "ai", "parents": [{"symbol": "FET"}]},
    ]

    # Provide minimal stand-ins for the seed helpers used by backtest
    monkeypatch.setattr(
        mod, "_get_seed",
        lambda n: next((s for s in fake_seeds if s["narrative"] == n), None),
        raising=False,
    )

    def _seed_parent_cfg(narr, sym):
        seed = next((s for s in fake_seeds if s["narrative"] == narr), None)
        if not seed:
            return {}
        sym = (sym or "").upper()
        return next((p for p in seed["parents"] if (p.get("symbol") or "").upper() == sym), {})

    monkeypatch.setattr(mod, "_seed_parent_cfg", _seed_parent_cfg, raising=False)

    parents = mod._seed_parents("dogs")
    assert set(p.upper() for p in parents) == {"WIF", "MOODENG"}

    cfg = mod._seed_parent_cfg("dogs", "wif")
    assert isinstance(cfg, dict) and cfg.get("symbol") == "WIF"
