import pytest
from fastapi import HTTPException

# Import the exact function under test
from app.deps.auth import require_refresh_auth

def test_auth_env_disabled_returns_none(monkeypatch):
    # Ensure the "env not set" branch executes
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    assert require_refresh_auth(authorization=None) is None

def test_auth_missing_header_branch(monkeypatch):
    # REFRESH_TOKEN set + no header -> raises (hits one missed line)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization=None)

def test_auth_wrong_scheme_branch(monkeypatch):
    # Wrong scheme -> raises (hits another missed line)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Token nope")

def test_auth_wrong_token_branch(monkeypatch):
    # Bearer but wrong token -> raises (hits the third missed line)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Bearer nope")

def test_auth_success_branch(monkeypatch):
    # Bearer token matches -> success path covered
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    assert require_refresh_auth(authorization="Bearer s3cr3t") is None
