import os
import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import Headers

from app.deps.auth import require_refresh_token


def _make_request(headers: dict[str, str]) -> Request:
    """Helper to build a minimal Request with custom headers."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def test_require_refresh_token_missing_bearer(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    req = _make_request({"authorization": "notbearer abc"})
    with pytest.raises(HTTPException) as e:
        require_refresh_token(req)
    assert "missing bearer" in str(e.value.detail)


def test_require_refresh_token_invalid_token(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    req = _make_request({"authorization": "Bearer wrong"})
    with pytest.raises(HTTPException) as e:
        require_refresh_token(req)
    assert "invalid token" in str(e.value.detail)


def test_require_refresh_token_success(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "s3cr3t")
    req = _make_request({"authorization": "Bearer s3cr3t"})
    # should not raise
    assert require_refresh_token(req) is None
