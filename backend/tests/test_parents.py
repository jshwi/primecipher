import random
from app.parents import synthesize_parents, refresh_all
from app.seeds import list_narrative_names
from app.storage import get_parents

def test_synthesize_parents_deterministic(monkeypatch):
    def fake_randint(a, b):
        if (a, b) == (2, 6):
            return 3
        return 11
    monkeypatch.setattr(random, "randint", fake_randint)
    out = synthesize_parents()
    assert set(out.keys()) >= set(list_narrative_names())
    dogs = out.get("dogs", [])
    assert len(dogs) == 3
    assert all("parent" in x and "matches" in x for x in dogs)
    assert dogs == sorted(dogs, key=lambda x: -x["matches"])

def test_refresh_all_writes_storage(monkeypatch):
    def fake_randint(a, b):
        if (a, b) == (2, 6):
            return 2
        return 5
    monkeypatch.setattr(random, "randint", fake_randint)
    refresh_all()
    assert len(get_parents("moodeng")) == 2
