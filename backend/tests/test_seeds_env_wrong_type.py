import json
import os
import tempfile
import importlib


def test_load_narrative_seeds_env_wrong_json_type(monkeypatch):
    # Provide a valid JSON, but with a wrong top-level type (dict, not list)
    bad = {"narrative": "demo", "parents": [{"symbol": "DEMO"}]}

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "seeds.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(bad, f)

        monkeypatch.setenv("NARRATIVES_SEEDS_FILE", p)

        mod = importlib.import_module("app.seeds")
        importlib.reload(mod)

        seeds = mod.load_narrative_seeds()
        # Tolerant: loader should not crash; it may fallback/return []
        assert isinstance(seeds, list)
