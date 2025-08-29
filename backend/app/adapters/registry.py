from __future__ import annotations
from typing import Callable, Dict, Type, List, Any

_REGISTRY: Dict[str, Callable[[], Any]] = {}

def register_adapter(name: str):
    """Decorator to register an adapter factory under a stable name."""
    def _wrap(factory: Callable[[], Any]):
        key = name.lower().strip()
        if not key:
            raise ValueError("adapter name cannot be empty")
        _REGISTRY[key] = factory
        return factory
    return _wrap

def get_adapter_names() -> List[str]:
    return sorted(_REGISTRY.keys())

def make_adapter(name: str):
    key = (name or "").lower().strip()
    if key not in _REGISTRY:
        raise KeyError(f"unknown adapter '{name}'")
    return _REGISTRY[key]()  # factory returns an instance
