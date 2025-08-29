import json, importlib

def _auth():
    return {"Authorization": "Bearer testtoken"}

def test_get_and_reload_seeds(client, monkeypatch, tmp_path):
    seeds1 = {"version": 2, "narratives": [
        {"name":"a","terms":{"include":["x"],"require_all":False,"synonyms":{}}, "block":[], "weight":1.0, "branches":[]}
    ]}
    f = tmp_path / "narratives.seed.json"
    f.write_text(json.dumps(seeds1), encoding="utf-8")
    monkeypatch.setenv("SEEDS_PATH", str(f))
    monkeypatch.setenv("REFRESH_TOKEN", "testtoken")

    import app.seeds as s; importlib.reload(s)
    import app.api.routes.seeds as r; importlib.reload(r)

    r1 = client.get("/seeds")
    assert r1.status_code == 200
    assert r1.json()["narratives"][0]["name"] == "a"

    # mutate file
    seeds2 = {"version": 2, "narratives": [
        {"name":"b","terms":{"include":["y"],"require_all":False,"synonyms":{}}, "block":[], "weight":1.0, "branches":[]}
    ]}
    f.write_text(json.dumps(seeds2), encoding="utf-8")

    r2 = client.post("/seeds/reload", headers=_auth())
    assert r2.status_code == 200
    assert r2.json()["narratives"][0]["name"] == "b"
