"""Tests for typed responses validation."""

import importlib


def test_parents_response_shape(client) -> None:
    """Test that parents response has correct shape and types.

    :param client: Pytest fixture for test client.
    """
    # happy path: types line up with schema
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200 and r.json()["ok"] is True
    # grab one narrative name from /narratives
    r2 = client.get("/narratives")
    name = r2.json()["items"][0]
    r3 = client.get(f"/parents/{name}")
    js = r3.json()
    assert isinstance(js["narrative"], str)
    assert isinstance(js["window"], str)
    assert isinstance(js["items"], list)
    assert (
        js["items"]
        and isinstance(js["items"][0]["parent"], str)
        and isinstance(js["items"][0]["matches"], int)
    )


def test_refresh_validation_rejects_bad_items(
    monkeypatch,
    client,
) -> None:
    """Test that refresh validation rejects invalid data.

    :param monkeypatch: Pytest fixture for patching.
    :param client: Pytest fixture for test client.
    """
    # monkeypatch source to emit invalid rows → should 500 via global
    # handler
    import app.adapters.source as src

    def bad(_self, _: str, __: list[str], **_kw):
        return [{"parent": "", "matches": -1}, {"parent": 123, "matches": "x"}]

    monkeypatch.setattr(src.Source, "parents_for", bad, raising=True)
    # reload parents module to ensure validation is used (not strictly
    # necessary)
    import app.parents as parents_mod

    importlib.reload(parents_mod)
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 500
    body = r.json()
    assert body.get("ok") is False
    assert body.get("error") == "internal_error"
