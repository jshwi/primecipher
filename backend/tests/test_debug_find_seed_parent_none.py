def test_find_seed_parent_none_when_no_narrative():
    import app.debug as dbg
    assert dbg._find_seed_parent(None, "ANY") is None
