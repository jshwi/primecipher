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
    # Discover an actual narrative that exists in this environment
    r_list = app_client.get("/narratives?source=file&window=24h")
    assert r_list.status_code == 200
    items = r_list.json()
    assert isinstance(items, list) and len(items) > 0

    # Grab the first narrative slug/key that the API exposes
    # Items may be dicts like {"narrative": "...", ...}
    slug = items[0].get("narrative") if isinstance(items[0], dict) else str(items[0])
    assert slug and isinstance(slug, str)

    # Now hit the parents endpoint with a slug we know exists
    r = app_client.get(f"/parents/{slug}?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # basic shape check
    assert len(data) >= 0
