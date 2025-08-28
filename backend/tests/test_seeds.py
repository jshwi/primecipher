from app.seeds import load_seeds, list_narrative_names

def test_load_seeds_shape():
    s = load_seeds()
    assert "narratives" in s
    assert isinstance(s["narratives"], list)
    assert all({"name","terms","allowNameMatch","block"} <= set(n.keys()) for n in s["narratives"])

def test_list_narrative_names_nonempty():
    names = list_narrative_names()
    assert isinstance(names, list)
    assert all(isinstance(x, str) for x in names)
