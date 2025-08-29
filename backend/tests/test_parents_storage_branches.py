import importlib

def test_refresh_fallback_and_setter_success(monkeypatch):
    """
    Hit fallback path (Source returns []), exercise set_parents success path.
    Covers ~58–59 (fallback) and normal set_parents write path.
    """
    import app.parents as parents_mod
    import app.adapters.source as source_mod
    import app.storage as storage_mod

    # Force adapter to return no data (fallback triggers)
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, name, terms: [])

    # Provide a working set_parents and a backing map
    calls = []
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)
    def _ok_set(narrative, items):
        calls.append(narrative)
        storage_mod._PARENTS[narrative] = list(items)
    monkeypatch.setattr(storage_mod, "set_parents", _ok_set, raising=False)

    out = parents_mod.refresh_all(dry_run=False)
    assert out and calls, "set_parents should have been called"
    # ensure something is in memory too
    from app.seeds import list_narrative_names
    from app.storage import get_parents
    names = list_narrative_names()
    assert get_parents(names[0]), "in-memory store should be populated"

def test_refresh_setter_raises_then_map_fallback(monkeypatch):
    """
    Make set_parents raise to cover the try/except around it (lines ~96–97),
    then ensure _PARENTS map path stores items (~109–111).
    """
    import app.parents as parents_mod
    import app.adapters.source as source_mod
    import app.storage as storage_mod

    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, name, terms: [])

    class Boom(Exception): ...
    def _boom_set(_, __):
        raise Boom("kaboom")
    monkeypatch.setattr(storage_mod, "set_parents", _boom_set, raising=False)
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)

    out = parents_mod.refresh_all(dry_run=False)
    assert out, "refresh should still succeed despite setter exception"
    from app.seeds import list_narrative_names
    names = list_narrative_names()
    assert names[0] in storage_mod._PARENTS  # map fallback wrote successfully

def test_refresh_map_raises_then_continue(monkeypatch):
    """
    Make _PARENTS assignment raise to cover its except branch (~116–117).
    """
    import app.parents as parents_mod
    import app.adapters.source as source_mod
    import app.storage as storage_mod

    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, name, terms: [])

    # No set_parents; only a map that raises on setitem
    class BoomDict(dict):
        def __setitem__(self, k, v):
            raise RuntimeError("boom")
    monkeypatch.setattr(storage_mod, "_PARENTS", BoomDict(), raising=False)
    if hasattr(storage_mod, "set_parents"):
        monkeypatch.delattr(storage_mod, "set_parents", raising=False)

    out = parents_mod.refresh_all(dry_run=False)
    assert out, "refresh should succeed even if map write fails"
