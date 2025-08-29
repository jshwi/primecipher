import importlib

def test_set_parents_success(monkeypatch):
    """Covers normal set_parents call inside refresh_all."""
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, n, t: [{"parent": "p", "matches": 1}])

    import app.storage as storage_mod
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)
    called = {}
    def _ok(n, items):
        called["yes"] = True
        storage_mod._PARENTS[n] = list(items)
    monkeypatch.setattr(storage_mod, "set_parents", _ok, raising=False)

    import app.parents as parents_mod
    importlib.reload(parents_mod)
    out = parents_mod.refresh_all(dry_run=False)
    assert out and called["yes"]

def test_set_parents_raises_then_map(monkeypatch):
    """Covers the try/except around set_parents, then map fallback."""
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, n, t: [{"parent": "p", "matches": 1}])

    import app.storage as storage_mod
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)
    def _boom(n, items):
        raise RuntimeError("boom")
    monkeypatch.setattr(storage_mod, "set_parents", _boom, raising=False)

    import app.parents as parents_mod
    importlib.reload(parents_mod)
    out = parents_mod.refresh_all(dry_run=False)
    # Even if set_parents fails, fallback to map should still work
    assert out
    from app.seeds import list_narrative_names
    from app.storage import get_parents
    names = list_narrative_names()
    assert get_parents(names[0])  # in-memory map populated

def test_map_assignment_raises(monkeypatch):
    """Covers the try/except around _PARENTS assignment."""
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, n, t: [{"parent": "p", "matches": 1}])

    import app.storage as storage_mod
    class BoomDict(dict):
        def __setitem__(self, k, v):
            raise RuntimeError("boom")
    monkeypatch.setattr(storage_mod, "_PARENTS", BoomDict(), raising=False)
    monkeypatch.setattr(storage_mod, "set_parents", None, raising=False)

    import app.parents as parents_mod
    importlib.reload(parents_mod)
    out = parents_mod.refresh_all(dry_run=False)
    assert out  # still returns scored items
