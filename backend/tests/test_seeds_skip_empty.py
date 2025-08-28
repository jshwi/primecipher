import json, os
from app import seeds as seeds_mod
from app.seeds import load_seeds

def test_seeds_skip_empty_name(tmp_path, monkeypatch):
    bad = {"narratives": [{"name": ""}, {"name": "ai", "terms": []}]}
    p = tmp_path / "narratives.seed.json"
    p.write_text(json.dumps(bad))

    monkeypatch.setenv("SEEDS_FILE", str(p))
    seeds_mod.load_seeds.cache_clear()

    s = load_seeds()
    names = [n["name"] for n in s["narratives"]]
    assert names == ["ai"]

    seeds_mod.load_seeds.cache_clear()
