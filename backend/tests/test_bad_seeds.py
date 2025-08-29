# backend/tests/test_bad_seeds.py
import json, pytest
import app.seeds as s
from pathlib import Path

def test_invalid_seeds_file(monkeypatch, tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"foo": "bar"}))
    monkeypatch.setenv("SEEDS_PATH", str(f))
    with pytest.raises(ValueError):
        s.get_seeds.cache_clear()
        s.get_seeds()
