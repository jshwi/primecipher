import pytest
from fastapi import HTTPException
from app.deps.auth import require_refresh_auth

def test_auth_missing_header_branch(monkeypatch):
    # REFRESH_TOKEN is set but no header provided -> raises (covers one branch)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization=None)

def test_auth_wrong_scheme_branch(monkeypatch):
    # Header present but wrong scheme (Token ...) -> raises (covers second branch)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Token nope")

def test_auth_wrong_token_branch(monkeypatch):
    # Bearer present but token mismatch -> raises (covers third branch)
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException):
        require_refresh_auth(authorization="Bearer bad")
