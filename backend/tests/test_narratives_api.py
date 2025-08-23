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

def test_parents_file_source(app_client):
    r = app_client.get("/parents/dogs?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
