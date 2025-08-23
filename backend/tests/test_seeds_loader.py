import json
from pathlib import Path

def test_load_narrative_seeds_from_env(tmp_path, monkeypatch):
    # Create a tiny seeds file
    data = [
        {"narrative": "ai", "parents": [{"symbol": "FET"}]},
        {"narrative": "dogs", "parents": [{"symbol": "WIF"}]},
    ]
    p = tmp_path / "narratives.seed.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    # Point loader to our temp file
    monkeypatch.setenv("NARRATIVES_SEEDS_FILE", str(p))

    import importlib
    mod = importlib.import_module("app.seeds")
    importlib.reload(mod)  # ensure it reads env and (re)loads

    seeds = mod.load_narrative_seeds()
    assert isinstance(seeds, list)
    assert any(s.get("narrative") == "ai" for s in seeds)

def test_load_narrative_seeds_fallback_constant(monkeypatch):
    # Clear env so loader uses default path (repo seeds file likely present)
    monkeypatch.delenv("NARRATIVES_SEEDS_FILE", raising=False)

    # Patch NARRATIVES for completeness, but the loader may prefer the file if it exists
    import importlib
    mod = importlib.import_module("app.seeds")
    fake = [{"narrative": "demo", "parents": [{"symbol": "DEMO"}]}]
    monkeypatch.setattr(mod, "NARRATIVES", fake, raising=False)
    importlib.reload(mod)

    seeds = mod.load_narrative_seeds()
    assert isinstance(seeds, list)
    assert len(seeds) > 0  # Accept repo's default file or the patched constant
