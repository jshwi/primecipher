"""Tests for refresh authentication."""


def test_refresh_auth_optional(client, monkeypatch) -> None:
    """Test that refresh is open when no token is configured.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # no token configured => refresh is open
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_refresh_auth_required(client, monkeypatch) -> None:
    """Test that refresh requires authentication when token is configured.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    # missing header -> 401
    r = client.post("/refresh")
    assert r.status_code == 401
    body = r.json()
    assert body.get("ok") is False and "error" in body
    # wrong header -> 401
    r2 = client.post("/refresh", headers={"Authorization": "Bearer nope"})
    assert r2.status_code == 401
    # correct header -> 200
    r3 = client.post("/refresh", headers={"Authorization": "Bearer s3cr3t"})
    assert r3.status_code == 200
    assert r3.json().get("ok") is True
