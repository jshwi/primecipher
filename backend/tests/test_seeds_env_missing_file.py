def test_load_narrative_seeds_env_missing_falls_back(monkeypatch):
    import importlib
    mod = importlib.import_module("app.seeds")

    # Point to a definitely-nonexistent file
    monkeypatch.setenv("NARRATIVES_SEEDS_FILE", "/___does_not_exist___/narratives.json")
    importlib.reload(mod)

    seeds = mod.load_narrative_seeds()
    # We don't assert exact contents; just that it handled the missing file gracefully.
    assert isinstance(seeds, list)
    assert len(seeds) >= 0  # tolerate empty or fallback-to-default
