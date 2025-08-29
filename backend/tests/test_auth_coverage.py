def test_refresh_wrong_scheme_rejected(client, monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    r = client.post("/refresh", headers={"Authorization": "Token nope"})
    assert r.status_code == 401
    body = r.json()
    # Accept either error or detail depending on how the app is implemented
    msg = body.get("detail") or body.get("error", "")
    assert "invalid" in msg.lower() or "missing" in msg.lower()
