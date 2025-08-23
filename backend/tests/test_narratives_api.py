def test_narratives_file_source(app_client):
    r = app_client.get("/narratives?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    items = data.get("narratives", [])
    assert isinstance(items, list)
    names = {row.get("key") or row.get("narrative") for row in items}
    assert {"dogs", "ai"} <= names

def test_parents_ai_file_source(app_client):
    r = app_client.get("/parents/ai?source=file&window=24h")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    parents = {row["parent"] for row in rows}
    assert {"FET", "TAO"} <= parents

