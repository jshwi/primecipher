from typing import List
import base64, json

def _enc_cursor(n: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"o": n}).encode()).decode()

def _fake_many(_self, narrative: str, terms: List[str], **_kw):
    # 150 ascending matches; route will cap to TOP_N=100
    return [{"parent": f"p{i:03d}", "matches": i} for i in range(150)]

def test_parents_pagination_two_pages(client, monkeypatch):
    # Patch Source actually used by compute_all()
    import app.parents as parents_mod
    monkeypatch.setattr(parents_mod.Source, "parents_for", _fake_many, raising=True)

    # Persist data (not dryRun) so route reads DB path too
    r = client.post("/refresh")
    assert r.status_code == 200

    # Page 1
    r1 = client.get("/parents/dogs?limit=25")
    assert r1.status_code == 200
    b1 = r1.json()
    assert len(b1["items"]) == 25
    assert b1["nextCursor"] is not None

    # Page 2 via returned cursor
    cursor = b1["nextCursor"]
    r2 = client.get(f"/parents/dogs?limit=25&cursor={cursor}")
    assert r2.status_code == 200
    b2 = r2.json()
    assert len(b2["items"]) == 25
    # Ensure no overlap between pages
    first_ids = {x["parent"] for x in b1["items"]}
    second_ids = {x["parent"] for x in b2["items"]}
    assert first_ids.isdisjoint(second_ids)

def test_parents_pagination_end_of_list(client, monkeypatch):
    import app.parents as parents_mod
    monkeypatch.setattr(parents_mod.Source, "parents_for", _fake_many, raising=True)
    client.post("/refresh")

    # Jump close to end (100 capped items total)
    cursor = _enc_cursor(90)
    r = client.get(f"/parents/dogs?limit=25&cursor={cursor}")
    assert r.status_code == 200
    b = r.json()
    # Only 10 remain (items 90..99)
    assert len(b["items"]) == 10
    assert b["nextCursor"] is None

def test_parents_invalid_cursor_400(client):
    r = client.get("/parents/dogs?cursor=not-base64")
    assert r.status_code == 400
    body = r.json()
    # Your global handler wraps HTTPException into {"ok": false, "error": "..."}
    assert body.get("ok") is False
    assert "error" in body
