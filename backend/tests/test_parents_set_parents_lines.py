import importlib

def test_refresh_calls_set_parents_success(monkeypatch):
    """
    Explicitly hit the set_parents success path in parents.refresh_all
    (the two missed lines ~96–97).
    """
    # Make Source return one item so we go through scoring
    import app.adapters.source as source_mod
    monkeypatch.setattr(
        source_mod.Source, "parents_for",
        lambda self, n, t: [{"parent": "x", "matches": 1}]
    )

    # Provide a set_parents that is actually called
    import app.storage as storage_mod
    called = {"hit": False}
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)

    def _set(narrative, items):
        called["hit"] = True
        storage_mod._PARENTS[narrative] = list(items)

    monkeypatch.setattr(storage_mod, "set_parents", _set, raising=False)

    # Reload parents to ensure coverage maps to current line numbers
    import app.parents as parents_mod
    importlib.reload(parents_mod)

    # Non-dry run so persistence & in-memory updates happen
    out = parents_mod.refresh_all(dry_run=False)
    assert out and called["hit"] is True
