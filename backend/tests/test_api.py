from fastapi.testclient import TestClient
from app.storage import get_parents, last_refresh_ts
from app.parents import refresh_all

def test_healthz():
    from app.main import app
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ready") is True

def test_narratives_list():
    from app.main import app
    c = TestClient(app)
    r = c.get("/narratives")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js
    assert isinstance(js["items"], list)

def test_parents_404_unknown():
    from app.main import app
    c = TestClient(app)
    r = c.get("/parents/__nope__")
    assert r.status_code == 404

def test_refresh_then_parents_flow(monkeypatch):
    from app.main import app
    import random

    def fake_randint(a, b):
        if (a, b) == (2, 6):
            return 3
        return 10

    monkeypatch.setattr(random, "randint", fake_randint)

    c = TestClient(app)
    r = c.post("/refresh")
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert last_refresh_ts() > 0

    for n in ("dogs", "ai"):
        r2 = c.get(f"/parents/{n}")
        assert r2.status_code == 200
        items = r2.json().get("items")
        assert isinstance(items, list)
        assert len(items) == 3
        assert all("parent" in x and "matches" in x for x in items)

def test_refresh_all_populates_store(monkeypatch):
    import random
    def fake_randint(a, b):
        if (a, b) == (2, 6):
            return 2
        return 7
    monkeypatch.setattr(random, "randint", fake_randint)
    refresh_all()
    assert len(get_parents("dogs")) == 2
