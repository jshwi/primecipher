import importlib

def test_set_parents_call_is_executed(monkeypatch):
    """
    Covers parents.py lines 96–97: the try-block that calls storage.set_parents(...)
    """
    # Force Source to return something (doesn't matter what)
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, name, terms: [{"parent": "x", "matches": 1}])

    # Provide a storage.set_parents so the call path is taken
    import app.storage as storage_mod
    called = {"ok": False}
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)
    def _set(narrative, items):
        called["ok"] = True
        storage_mod._PARENTS[narrative] = list(items)
    monkeypatch.setattr(storage_mod, "set_parents", _set, raising=False)

    # Reload parents to ensure line numbers & code map
    import app.parents as parents_mod
    importlib.reload(parents_mod)

    out = parents_mod.refresh_all(dry_run=False)
    assert out and called["ok"] is True
