def test_refresh_auth_optional(client, monkeypatch):
    # No token configured => refresh is open
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_refresh_auth_required(client, monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    # Missing header -> 401
    r = client.post("/refresh")
    assert r.status_code == 401
    body = r.json()
    assert body.get("ok") is False and "error" in body
    # Wrong header -> 401
    r2 = client.post("/refresh", headers={"Authorization": "Bearer nope"})
    assert r2.status_code == 401
    # Correct header -> 200
    r3 = client.post("/refresh", headers={"Authorization": "Bearer s3cr3t"})
    assert r3.status_code == 200
    assert r3.json().get("ok") is True
