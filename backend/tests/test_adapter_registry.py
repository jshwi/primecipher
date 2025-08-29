import importlib, os, pytest

def test_registry_lists_modes():
    import app.adapters.source as src
    names = src.Source.available()
    # minimal set we promise
    assert {"test", "dev", "coingecko"}.issubset(set(names))

def test_source_uses_env_mode(monkeypatch):
    import app.adapters.source as src
    monkeypatch.setenv("SOURCE_MODE", "test")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog"])
    # deterministic "test" provider returns exactly 3
    assert len(out) == 3

def test_source_provider_override(monkeypatch):
    import app.adapters.source as src
    monkeypatch.setenv("SOURCE_MODE", "dev")
    importlib.reload(src)
    # construct with explicit provider name to override env
    s = src.Source(provider="test")
    out = s.parents_for("dogs", ["dog"])
    assert len(out) == 3  # from deterministic

def test_unknown_provider_raises(monkeypatch):
    import app.adapters.source as src
    with pytest.raises(KeyError):
        src.Source(provider="nope-123")
