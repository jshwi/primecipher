# backend/tests/test_seeds_v2.py
import json, importlib

def test_v2_parse_and_names(monkeypatch, tmp_path):
    data = {
        "version": 2,
        "narratives": [
            {"name": "x", "terms": {"include": ["a"], "require_all": False, "synonyms": {}}, "block": [], "weight": 1.0, "branches": []}
        ]
    }
    p = tmp_path / "narratives.seed.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("SEEDS_PATH", str(p))
    import app.seeds as s; importlib.reload(s)
    ss = s.get_seeds()
    assert [n.name for n in ss.narratives] == ["x"]
