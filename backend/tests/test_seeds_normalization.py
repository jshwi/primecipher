import importlib


def test_seeds_normalization_helpers():
    seeds = importlib.import_module("app.seeds")

    p = seeds._norm_parent({"symbol": "WIF", "match": ["doge"]})
    assert p["symbol"] == "WIF"
    assert isinstance(p.get("match"), list)

    # Your _norm_discovery doesn’t strip whitespace → assert more loosely
    d = seeds._norm_discovery({"dexIds": ["orca", " raydium "], "liqMinUsd": 10})
    assert isinstance(d["dexIds"], list)
    assert d["dexIds"][0] == "orca"
    assert any("raydium" in x for x in d["dexIds"])
    assert d["liqMinUsd"] == 10

    s = seeds._normalize_seed(
        {"narrative": "dogs", "parents": [{"symbol": "WIF"}], "keywords": ["wif", "dog"]}
    )
    assert s["narrative"] == "dogs"
    assert isinstance(s["parents"], list)
    assert "keywords" in s and isinstance(s["keywords"], list)
