from app.storage import (
    get_parents,
    last_refresh_ts,
    mark_refreshed,
    set_parents,
)


def test_set_get_parents_roundtrip():
    set_parents("x", [{"parent": "p1", "matches": 1}])
    v = get_parents("x")
    assert v == [{"parent": "p1", "matches": 1}]


def test_mark_refreshed_sets_ts():
    mark_refreshed()
    assert last_refresh_ts() > 0
