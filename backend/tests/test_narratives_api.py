import app.seeds as seeds

def test_narratives_file_source(app_client):
    r = app_client.get("/narratives?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    items = data.get("narratives", [])
    assert isinstance(items, list)
    names = {row.get("key") or row.get("narrative") for row in items}
    assert {"dogs", "ai"} <= names

def test_parents_file_source(monkeypatch):
    # 1) Ensure seeds contain the narrative we call
    import app.seeds as seeds
    fake_seeds = [{"narrative": "dogs", "terms": ["dogs"], "block": [], "allowNameMatch": True}]
    monkeypatch.setattr(seeds, "NARRATIVES", fake_seeds, raising=False)

    # 2) (Optional but safe) set test-mode env for any guarded code paths
    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")

    # 3) Reload the FastAPI app *after* patching seeds so routes mount with our narrative
    import importlib
    import app.main as main
    importlib.reload(main)

    # 4) Use a fresh TestClient bound to the reloaded app
    from fastapi.testclient import TestClient
    client = TestClient(main.app)

    r = client.get("/parents/dogs?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any("dogs" in str(p).lower() for p in data)
