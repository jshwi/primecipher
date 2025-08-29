import os

def test_refresh_allows_when_env_not_set(client, monkeypatch):
    # No REFRESH_TOKEN -> endpoint should allow access (hits the "no env" branch)
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    r = client.post("/refresh", params={"dryRun": "true"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True

def test_refresh_missing_header_when_env_set(client, monkeypatch):
    # REFRESH_TOKEN set but no Authorization header -> 401 (missing/invalid header branch)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    r = client.post("/refresh", params={"dryRun": "true"})
    assert r.status_code == 401

def test_refresh_wrong_token_when_env_set(client, monkeypatch):
    # REFRESH_TOKEN set + wrong Bearer token -> 401 (invalid token branch)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    r = client.post("/refresh", params={"dryRun": "true"},
                    headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
