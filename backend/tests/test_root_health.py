def test_root_page(app_client):
    r = app_client.get("/")
    # Baseline has no landing route; allow 404 or 200
    assert r.status_code in (200, 404)

def test_healthz(app_client):
    r = app_client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True

