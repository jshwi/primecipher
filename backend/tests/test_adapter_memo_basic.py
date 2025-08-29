def test_memo_across_narratives_same_terms(monkeypatch):
    # Count calls into the raw producer
    calls = {"n": 0}

    import app.adapters.source as src

    def fake_det(narrative, terms):
        calls["n"] += 1
        return [{"parent": "X", "matches": 10}, {"parent": "Y", "matches": 9}]

    # Force 'test' provider (deterministic) and patch its raw producer
    monkeypatch.setenv("SOURCE_MODE", "test")
    # ensure fresh module constants
    import importlib
    importlib.reload(src)
    monkeypatch.setattr(src, "_deterministic_items", fake_det, raising=True)

    s = src.Source()  # uses provider 'test'
    # Two different narratives, same terms -> one underlying fetch
    s.parents_for("dogs", ["Dog", "wif"])
    s.parents_for("puppies", ["wif", "dog"])  # different order/case

    assert calls["n"] == 1  # memo hit on second call
