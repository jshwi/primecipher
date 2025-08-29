import importlib

def test_parents_fallback_and_set_parents_success(monkeypatch):
    """
    Force adapter to yield [], triggering fallback (58–59), run through compute_all()
    to hit its return (77), then ensure set_parents success path is executed (96–97).
    """
    # 1) Force Source.parents_for -> [] to trigger fallback path
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for", lambda self, name, terms: [])

    # 2) Provide a working set_parents and a backing map in storage
    import app.storage as storage_mod
    called = {"ok": False}
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)

    def _ok_set(narrative, items):
        called["ok"] = True
        storage_mod._PARENTS[narrative] = list(items)

    monkeypatch.setattr(storage_mod, "set_parents", _ok_set, raising=False)

    # Reload parents module to ensure we hit fresh code
    import app.parents as parents_mod
    importlib.reload(parents_mod)

    # 3) Run refresh (non-dry) to traverse all the lines
    out = parents_mod.refresh_all(dry_run=False)

    # 4) Assertions: set_parents was called and in-memory store got data
    assert out and called["ok"] is True
    from app.seeds import list_narrative_names
    from app.storage import get_parents
    names = list_narrative_names()
    assert names, "seeds should define at least one narrative"
    saved = get_parents(names[0])
    assert isinstance(saved, list) and len(saved) > 0
    # also confirm scoring produced floats
    assert all(isinstance(it.get("score"), float) for it in saved)
