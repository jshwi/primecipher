"""Tests for adapter registry functionality."""

import importlib

import pytest


def test_registry_lists_modes() -> None:
    """Test that registry lists available modes."""
    import app.adapters.source as src

    names = src.Source.available()
    # minimal set we promise
    assert {"test", "dev", "coingecko"}.issubset(set(names))


def test_source_uses_env_mode(monkeypatch) -> None:
    """Test that source uses environment mode by default.

    :param monkeypatch: Pytest fixture for patching.
    """
    import app.adapters.source as src

    monkeypatch.setenv("SOURCE_MODE", "test")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog"])
    # deterministic "test" provider returns exactly 3
    assert len(out) == 3


def test_source_provider_override(monkeypatch) -> None:
    """Test that explicit provider overrides environment mode.

    :param monkeypatch: Pytest fixture for patching.
    """
    import app.adapters.source as src

    monkeypatch.setenv("SOURCE_MODE", "dev")
    importlib.reload(src)
    # construct with explicit provider name to override env
    s = src.Source(provider="test")
    out = s.parents_for("dogs", ["dog"])
    assert len(out) == 3  # from deterministic


def test_unknown_provider_raises() -> None:
    """Test that unknown provider raises KeyError."""
    import app.adapters.source as src

    with pytest.raises(KeyError):
        src.Source(provider="nope-123")
