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
    payload = r_list.json()
    items = payload.get("narratives", [])
    assert isinstance(items, list) and len(items) > 0

    # Use the first narrative's slug (prefer 'key', fallback to 'narrative')
    first = items[0]
    slug = first.get("key") or first.get("narrative")
    assert isinstance(slug, str) and slug

    # Now hit the parents endpoint with a known-good slug
    r = app_client.get(f"/parents/{slug}?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
