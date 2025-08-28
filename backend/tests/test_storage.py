from app.storage import set_parents, get_parents, mark_refreshed, last_refresh_ts

def test_set_get_parents_roundtrip():
    set_parents("x", [{"parent":"p1","matches":1}])
    v = get_parents("x")
    assert v == [{"parent":"p1","matches":1}]

def test_mark_refreshed_sets_ts():
    mark_refreshed()
    assert last_refresh_ts() > 0
