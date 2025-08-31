"""Tests for adapter registry extra functionality."""

import pytest


def test_register_empty_name_raises() -> None:
    """Test that registering an adapter with empty name raises ValueError."""
    from backend.adapters import registry

    with pytest.raises(ValueError):

        @registry.register_adapter("")  # decorator should raise immediately
        def _dummy() -> object:
            return object()


def test_make_adapter_unknown_raises() -> None:
    """Test that making an unknown adapter raises KeyError."""
    from backend.adapters import registry

    with pytest.raises(KeyError):
        registry.make_adapter("nope-xyz")


def test_get_adapter_names_includes_builtins() -> None:
    """Test that adapter names include builtins and are sorted."""
    from backend.adapters import registry

    names = registry.get_adapter_names()
    # ensure core modes are present and list is sorted
    assert {"test", "dev", "coingecko"}.issubset(set(names))
    assert names == sorted(names)
