from time import time
from app.repo import replace_parents, list_parents
from app.seeds import list_narrative_names

def test_replace_and_list_parents_roundtrip():
    narrative = list_narrative_names()[0]  # e.g. 'dogs'
    items = [{"parent": "p1", "matches": 5}, {"parent": "p2", "matches": 7}]
    ts = time()
    replace_parents(narrative, items, ts)

    rows = list_parents(narrative)
    assert rows == sorted(items, key=lambda x: -x["matches"])

def test_replace_parents_overwrites_previous():
    narrative = list_narrative_names()[0]
    replace_parents(narrative, [{"parent": "old", "matches": 1}], time())
    replace_parents(narrative, [{"parent": "new", "matches": 9}], time())
    rows = list_parents(narrative)
    assert rows == [{"parent": "new", "matches": 9}]
