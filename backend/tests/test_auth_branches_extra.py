import pytest
from fastapi import HTTPException
from app.deps.auth import require_refresh_auth

def test_auth_missing_header(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "zzz")
    with pytest.raises(HTTPException):
        require_refresh_auth(None)

def test_auth_wrong_scheme(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "zzz")
    with pytest.raises(HTTPException):
        require_refresh_auth("Token nope")

def test_auth_wrong_token(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "zzz")
    with pytest.raises(HTTPException):
        require_refresh_auth("Bearer nope")
