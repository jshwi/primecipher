import pytest
from fastapi import HTTPException
from app.deps.auth import require_refresh_auth

def test_auth_missing_header_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization=None)

def test_auth_wrong_scheme_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Token nope")

def test_auth_wrong_token_raises(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Bearer bad")

def test_auth_success_returns_none(monkeypatch):
    # Also cover the success path so the function body is fully exercised
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    assert require_refresh_auth(authorization="Bearer s3cr3t") is None
