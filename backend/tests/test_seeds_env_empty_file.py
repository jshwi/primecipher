import os
import tempfile
import importlib


def test_load_narrative_seeds_env_empty_file(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "seeds.json")
        # touch an empty file
        open(p, "w", encoding="utf-8").close()

        monkeypatch.setenv("NARRATIVES_SEEDS_FILE", p)
        mod = importlib.import_module("app.seeds")
        importlib.reload(mod)

        seeds = mod.load_narrative_seeds()
        assert isinstance(seeds, list)
