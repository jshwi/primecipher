import os
import tempfile
import importlib


def test_load_narrative_seeds_env_is_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        # Point env var at a directory (open() should fail; loader must not crash)
        monkeypatch.setenv("NARRATIVES_SEEDS_FILE", d)

        mod = importlib.import_module("app.seeds")
        importlib.reload(mod)

        seeds = mod.load_narrative_seeds()
        assert isinstance(seeds, list)
