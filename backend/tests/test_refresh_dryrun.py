from app.storage import last_refresh_ts

def test_refresh_dry_run_does_not_persist(client):
    before = last_refresh_ts()
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and body.get("dryRun") is True
    assert body.get("items") and isinstance(body["items"], dict)
    # ts unchanged because we didn't mark_refreshed
    assert last_refresh_ts() == before
