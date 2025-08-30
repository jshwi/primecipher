"""Tests for version and meta functionality."""

import importlib

import app.version


def test_version_env_override(monkeypatch, client):
    """Test that version endpoint respects environment variable overrides."""
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setenv("BUILT_AT", "2025-08-28T12:00:00Z")
    importlib.reload(app.version)

    r = client.get("/version")
    assert r.status_code == 200
    v = r.json()["version"]
    assert v["git"] == "abc123"
    assert v["builtAt"] == "2025-08-28T12:00:00Z"
