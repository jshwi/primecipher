"""Tests for source modes functionality."""

# backend/tests/test_source_modes.py
import importlib

import backend.adapters.source as src


def test_source_test_mode(monkeypatch) -> None:
    """Test source test mode returns deterministic results.

    :param monkeypatch: Pytest fixture for patching.
    """
    monkeypatch.setenv("SOURCE_MODE", "test")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog", "wif", "shib"])
    assert [x["matches"] for x in out] == [11, 10, 9]


def test_source_dev_mode_shape(monkeypatch) -> None:
    """Test source dev mode returns valid data structure.

    :param monkeypatch: Pytest fixture for patching.
    """
    monkeypatch.setenv("SOURCE_MODE", "dev")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog", "wif", "shib"])
    assert 2 <= len(out) <= 6
    assert all(isinstance(x.get("matches"), int) for x in out)
