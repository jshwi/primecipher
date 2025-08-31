"""Tests for CORS and error handling."""

from backend.main import _parse_origins  # internal helper is importable


def test_cors_parse_multiple_env(monkeypatch) -> None:
    """Test CORS origins parsing from environment variable.

    :param monkeypatch: Pytest fixture for patching.
    """
    monkeypatch.setenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000, https://example.com",
    )
    assert _parse_origins() == ["http://localhost:3000", "https://example.com"]


def test_internal_error_envelope(client) -> None:
    """Test internal error returns proper error envelope.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/__boom_for_tests__")
    assert r.status_code == 500
    assert r.json() == {"ok": False, "error": "internal_error"}
