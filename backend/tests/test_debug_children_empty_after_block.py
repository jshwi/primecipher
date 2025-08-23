import app.debug as dbg

def test_debug_children_empty_after_block(monkeypatch):
    # Seed with a blocklist that removes the only child
    seeds_data = [{"narrative": "ai", "parents": [{"symbol": "FET", "block": ["ONLY"]}]}]
    monkeypatch.setattr(dbg, "load_narrative_seeds", lambda: seeds_data, raising=False)

    class FakeAdapter:
        def fetch_children_for_parent(self, **kw):
            return [{"symbol": "ONLY"}]  # will be blocked

    monkeypatch.setattr(dbg, "make_onchain_adapter", lambda _p: FakeAdapter(), raising=False)

    out = dbg.debug_children(
        parent="FET",
        narrative="ai",
        applyBlocklist=True,
        allowNameMatch=None,
        dexIds=None,          # ensure not a fastapi.Query object
        volMinUsd=None,       # "
        liqMinUsd=None,       # "
        maxAgeHours=None,     # "
        limit=10,
        offset=0,
    )
    assert out["counts"]["total"] == 1
    assert out["counts"]["returned"] == 0
    assert out["children"] == []
