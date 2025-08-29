import pytest

def test_register_empty_name_raises():
    from app.adapters import registry
    with pytest.raises(ValueError):
        @registry.register_adapter("")   # decorator should raise immediately
        def _dummy():
            return object()

def test_make_adapter_unknown_raises():
    from app.adapters import registry
    with pytest.raises(KeyError):
        registry.make_adapter("nope-xyz")

def test_get_adapter_names_includes_builtins():
    from app.adapters import registry
    names = registry.get_adapter_names()
    # Ensure core modes are present and list is sorted
    assert {"test", "dev", "coingecko"}.issubset(set(names))
    assert names == sorted(names)
