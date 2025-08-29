import random
from app.storage import last_refresh_ts

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ready") is True

def test_narratives_list(client):
    r = client.get("/narratives")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and isinstance(js["items"], list)

def test_parents_404_unknown(client):
    r = client.get("/parents/__nope__")
    assert r.status_code == 404

from app.seeds import list_narrative_names

def test_refresh_then_parents_flow(client):
    r = client.post("/refresh")
    assert r.status_code == 200 and r.json().get("ok") is True

    for n in list_narrative_names():  # no hardcoded 'moodeng'
        r2 = client.get(f"/parents/{n}")
        assert r2.status_code == 200
        items = r2.json().get("items")
        assert isinstance(items, list) and len(items) > 0
        for it in items:
            assert "parent" in it and "matches" in it and "score" in it
