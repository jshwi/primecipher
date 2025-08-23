import os
import tempfile
import importlib


def test_load_narrative_seeds_env_bad_json(monkeypatch):
    # Create a definitely-invalid JSON file
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "seeds.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write("{not: valid json!")

        monkeypatch.setenv("NARRATIVES_SEEDS_FILE", p)
        mod = importlib.import_module("app.seeds")
        importlib.reload(mod)

        seeds = mod.load_narrative_seeds()
        # Tolerant: just ensure it didn't crash and returns a list (fallback behavior)
        assert isinstance(seeds, list)
