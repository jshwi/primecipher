import importlib

def test_set_parents_success(monkeypatch):
    import app.adapters.source as source_mod
    # Always return one item
    monkeypatch.setattr(source_mod.Source, "parents_for",
                        lambda self, n, t: [{"parent": "x", "matches": 1}])

    import app.storage as storage_mod
    called = {}
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)

    def _ok(n, items):
        called["hit"] = True
        storage_mod._PARENTS[n] = list(items)

    monkeypatch.setattr(storage_mod, "set_parents", _ok, raising=False)

    import app.parents as parents_mod
    importlib.reload(parents_mod)

    out = parents_mod.refresh_all(dry_run=False)
    assert out and called.get("hit") is True
