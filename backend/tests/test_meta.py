def test_readyz(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"ready": True}

def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert "version" in body and "git" in body["version"] and "builtAt" in body["version"]
