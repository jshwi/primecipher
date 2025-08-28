import random
from app.parents import refresh_all
from app.seeds import list_narrative_names
from app.storage import get_parents
from app.parents import refresh_all
from app.storage import get_parents

def test_refresh_all_writes_storage():
    refresh_all()
    names = list_narrative_names()
    assert names, "no narratives defined in seeds"
    v = get_parents(names[0])
    assert isinstance(v, list) and len(v) == 3
