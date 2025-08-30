"""Adapter registry for managing different data source adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_REGISTRY: dict[str, Callable[[], Any]] = {}


def register_adapter(
    name: str,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """Decorator to register an adapter factory under a stable name.

    :param name: The name to register the adapter under.
    :return: The decorator function.
    """

    def _wrap(factory: Callable[[], Any]):
        key = name.lower().strip()
        if not key:
            raise ValueError("adapter name cannot be empty")
        _REGISTRY[key] = factory
        return factory

    return _wrap


def get_adapter_names() -> list[str]:
    """Get list of registered adapter names.

    :return: List of registered adapter names.
    """
    return sorted(_REGISTRY.keys())


def make_adapter(name: str) -> Any:
    """Create an adapter instance by name.

    :param name: The name of the adapter to create.
    :return: An instance of the requested adapter.
    :raises KeyError: If the adapter name is not found.
    """
    key = (name or "").lower().strip()
    if key not in _REGISTRY:
        raise KeyError(f"unknown adapter '{name}'")
    return _REGISTRY[key]()  # factory returns an instance
