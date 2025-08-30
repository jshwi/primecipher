"""Tests for meta endpoints."""


def test_readyz(client):
    """Test readyz endpoint returns ready status."""
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"ready": True}


def test_version(client):
    """Test version endpoint returns version information."""
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert (
        "version" in body
        and "git" in body["version"]
        and "builtAt" in body["version"]
    )
