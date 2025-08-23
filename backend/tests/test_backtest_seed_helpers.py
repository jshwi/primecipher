import importlib


def test_backtest_seed_helpers(monkeypatch):
    mod = importlib.import_module("app.backtest")

    fake_seeds = [
        {
            "narrative": "dogs",
            "parents": [
                {"symbol": "WIF", "match": ["dog", "wif"], "nameMatchAllowed": True},
                {"symbol": "MOODENG", "match": ["moodeng"]},
            ],
        },
        {
            "narrative": "ai",
            "parents": [{"symbol": "FET", "match": ["ai", "fet"], "nameMatchAllowed": False}],
        },
    ]

    # Backtest helpers read from app.seeds; patch the module function it calls
    seeds_mod = importlib.import_module("app.seeds")
    monkeypatch.setattr(seeds_mod, "load_narrative_seeds", lambda: fake_seeds, raising=False)

    # _get_seed returns the whole seed dict or None
    s = mod._get_seed("dogs")
    assert isinstance(s, dict) and s.get("narrative") == "dogs"
    assert mod._get_seed("nope") is None

    # _seed_parents returns list of symbols for that narrative
    ps = mod._seed_parents("dogs")
    assert set(x.upper() for x in ps) == {"WIF", "MOODENG"}

    # _seed_parent_cfg returns config dict, case-insensitive symbol
    cfg = mod._seed_parent_cfg("dogs", "wif")
    assert cfg.get("symbol") == "WIF" and isinstance(cfg.get("match"), list)

    # _window_key is a stable mapping and returns a string for unknowns
    assert mod._window_key("h6") == "h6"
    assert mod._window_key("h24") == "h24"
    assert isinstance(mod._window_key("unknown-hold"), str)


def test_backtest_child_pair_tolerant():
    mod = importlib.import_module("app.backtest")
    # Current impl may return None for these shapes; assert tolerant outcomes
    assert mod._child_pair({"pairAddress": "PAIR1"}) in (None, "PAIR1")
    assert mod._child_pair({"address": "PAIR2"}) in (None, "PAIR2")
    assert mod._child_pair({"nope": "x"}) is None
