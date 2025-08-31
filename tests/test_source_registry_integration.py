"""Tests for source registry integration."""


def test_source_available_and_override_env(monkeypatch) -> None:
    """Test that source registry works and explicit provider overrides env.

    :param monkeypatch: Pytest fixture for patching.
    """
    # force env to a different mode and ensure explicit provider wins
    import importlib

    monkeypatch.setenv("SOURCE_MODE", "dev")
    import backend.adapters.source as src

    importlib.reload(src)

    # available modes includes the ones we registered
    assert {"test", "dev", "coingecko"}.issubset(set(src.Source.available()))

    # explicit provider overrides env
    s = src.Source(provider="test")
    out = s.parents_for("dogs", ["dog"])
    assert (
        isinstance(out, list) and len(out) == 3
    )  # deterministic adapter shape
