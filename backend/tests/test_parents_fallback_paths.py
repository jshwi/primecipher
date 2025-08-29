import importlib
from types import SimpleNamespace

def test_refresh_fallback_and_storage_paths(monkeypatch):
    """
    Exercise parents.py branches:
      - Source.parents_for returns [] -> fallback executed   (lines ~58–59/77)
      - storage.set_parents exists -> called                (lines ~96–97)
      - storage._PARENTS map is also updated                (lines ~109–111/114–117)
    """
    # 1) Make the Source adapter return no data -> triggers fallback
    import app.parents as parents_mod
    import app.adapters.source as source_mod
    monkeypatch.setattr(source_mod.Source, "parents_for", lambda self, name, terms: [])

    # 2) Install a fake storage module API to hit both branches
    import app.storage as storage_mod
    calls = []
    # ensure the backing map exists and is empty
    monkeypatch.setattr(storage_mod, "_PARENTS", {}, raising=False)
    # expose a set_parents function that records calls
    def _fake_set_parents(narrative, items):
        calls.append((narrative, list(items)))
        # also reflect into the backing map like a realistic implementation
        storage_mod._PARENTS[narrative] = list(items)
    monkeypatch.setattr(storage_mod, "set_parents", _fake_set_parents, raising=False)

    # 3) Run a real refresh (non-dry-run to exercise full loop)
    out = parents_mod.refresh_all(dry_run=False)
    assert isinstance(out, dict) and out, "refresh should return a mapping"

    # 4) We should have invoked set_parents at least once
    assert calls, "storage.set_parents was not called"

    # 5) And _PARENTS should be populated for the first narrative name
    from app.seeds import list_narrative_names
    names = list_narrative_names()
    assert names, "no narratives configured"
    from app.storage import get_parents, _PARENTS  # type: ignore
    assert names[0] in _PARENTS
    saved = get_parents(names[0])
    assert isinstance(saved, list) and len(saved) > 0
    # Every saved item should have a numeric score (scoring path covered)
    assert all(isinstance(it.get("score"), float) for it in saved)
