import json, importlib
from pathlib import Path
from app import seeds as seeds_mod

def write_seeds(tmp_path, data):
    p = tmp_path / "narratives.seed.json"
    p.write_text(json.dumps(data))
    return p

def reload_seeds_with(path):
    import os
    os.environ["SEEDS_FILE"] = str(path)
    seeds_mod.load_seeds.cache_clear()
    importlib.reload(seeds_mod)

def test_blocklist_and_allow_name_match(tmp_path, client):
    # narrative 'dogs'; terms include 'dog'; block 'shib'
    data = {
        "narratives": [
            {"name": "dogs", "terms": ["dog", "wif", "shib"], "allowNameMatch": False, "block": ["shib"]}
        ]
    }
    p = write_seeds(tmp_path, data)
    reload_seeds_with(p)

    # dry run to compute without persisting
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    items = r.json()["items"]["dogs"]
    # ensure nothing containing 'shib' is present
    assert all("shib" not in i["parent"].lower() for i in items)
    # allowNameMatch=False: items that only match 'dogs' name (if any) are excluded;
    # deterministic adapter uses terms, so we still have up to 3 items left
    assert 0 <= len(items) <= 3
