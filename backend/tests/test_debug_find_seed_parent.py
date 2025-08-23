def test_find_seed_parent_found_and_missing(monkeypatch):
    import app.debug as dbg
    import app.seeds as seeds

    # Minimal seeds structure that dbg._find_seed_parent expects
    seeds_data = [
        {
            "narrative": "dogs",
            "parents": [
                {"symbol": "WIF", "address": "So11111111111111111111111111111111111111112"},
                {"symbol": "MOODENG", "address": "So2222222222222222222222222222222222222222"},
            ],
        },
        {
            "narrative": "ai",
            "parents": [
                {"symbol": "FET"},
                {"symbol": "TAO"},
            ],
        },
    ]

    # Force the module to see our deterministic seeds
    monkeypatch.setattr(seeds, "NARRATIVES", seeds_data, raising=False)

    # Found case
    out = dbg._find_seed_parent(narrative="dogs", parent_symbol="WIF")
    assert isinstance(out, dict)
    assert out.get("symbol") == "WIF"

    # Missing narrative
    out_none = dbg._find_seed_parent(narrative="cats", parent_symbol="WIF")
    assert out_none is None

    # Missing parent within a valid narrative
    out_none_2 = dbg._find_seed_parent(narrative="dogs", parent_symbol="NOTREAL")
    assert out_none_2 is None
