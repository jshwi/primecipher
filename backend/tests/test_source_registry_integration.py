def test_source_available_and_override_env(monkeypatch):
    # Force env to a different mode and ensure explicit provider wins
    import importlib
    monkeypatch.setenv("SOURCE_MODE", "dev")
    import app.adapters.source as src
    importlib.reload(src)

    # Available modes includes the ones we registered
    assert {"test", "dev", "coingecko"}.issubset(set(src.Source.available()))

    # Explicit provider overrides env
    s = src.Source(provider="test")
    out = s.parents_for("dogs", ["dog"])
    assert isinstance(out, list) and len(out) == 3  # deterministic adapter shape
