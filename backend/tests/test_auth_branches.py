import pytest
from fastapi import HTTPException
from app.deps.auth import require_refresh_auth

def test_missing_header_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException) as e:
        require_refresh_auth(authorization=None)
    assert "header" in str(e.value.detail).lower()

def test_wrong_scheme_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException) as e:
        require_refresh_auth(authorization="Token nope")
    assert "invalid" in str(e.value.detail).lower()

def test_wrong_token_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException) as e:
        require_refresh_auth(authorization="Bearer bad")
    assert "invalid" in str(e.value.detail).lower()
