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

def test_parents_ai_file_source(app_client, monkeypatch):
    # Force seeds to always include 'ai' so this test is deterministic
    fake_seeds = [{"narrative": "ai", "terms": ["ai"], "block": [], "allowNameMatch": True}]
    monkeypatch.setattr("app.seeds.NARRATIVES", fake_seeds, raising=False)

    r = app_client.get("/parents/ai?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()

    # The API returns a list of parents; check it's shaped correctly
    assert isinstance(data, list)
    assert any(p.get("narrative") == "ai" for p in data)
