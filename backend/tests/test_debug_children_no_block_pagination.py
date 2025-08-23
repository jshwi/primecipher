import app.debug as dbg


def test_debug_children_no_blocklist_empty_page(monkeypatch):
    # No seeds needed for this path; still set narrative to exercise seed lookup = None
    class FakeAdapter:
        def fetch_children_for_parent(self, **kw):
            # A couple of rows so pre-blocklist total > 0
            return [{"symbol": "OK1"}, {"symbol": "OK2"}]

    monkeypatch.setattr(dbg, "make_onchain_adapter", lambda _p: FakeAdapter(), raising=False)

    # applyBlocklist=False ⇒ no filtering; then pagination returns empty page with large offset
    out = dbg.debug_children(
        parent="FET",
        narrative=None,
        applyBlocklist=False,
        allowNameMatch=None,
        dexIds=None,
        volMinUsd=None,
        liqMinUsd=None,
        maxAgeHours=None,
        limit=2,
        offset=10,  # after filtering, page is empty
    )

    assert out["counts"]["total"] == 2         # pre-filter count
    assert out["counts"]["returned"] == 0      # empty page after pagination
    assert out["children"] == []
