# backend/tests/test_source_modes.py
import importlib, os
import app.adapters.source as src

def test_source_test_mode(monkeypatch):
    monkeypatch.setenv("SOURCE_MODE", "test")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog", "wif", "shib"])
    assert [x["matches"] for x in out] == [11, 10, 9]

def test_source_dev_mode_shape(monkeypatch):
    monkeypatch.setenv("SOURCE_MODE", "dev")
    importlib.reload(src)
    s = src.Source()
    out = s.parents_for("dogs", ["dog", "wif", "shib"])
    assert 2 <= len(out) <= 6
    assert all(isinstance(x.get("matches"), int) for x in out)
