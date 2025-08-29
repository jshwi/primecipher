def test_memo_normalizes_terms(monkeypatch):
    import importlib
    import app.adapters.source as src

    seen_keys = []
    def spy_det(narrative, terms):
        # record normalized terms used by memo (via returning distinct parents)
        return [{"parent": "|".join(sorted({t.lower() for t in terms})), "matches": 10}]

    monkeypatch.setenv("SOURCE_MODE", "test")
    monkeypatch.setenv("SOURCE_TTL", "60")
    importlib.reload(src)
    monkeypatch.setattr(src, "_deterministic_items", spy_det, raising=True)

    s = src.Source()
    a = s.parents_for("dogs", ["Dog", "wif"])
    b = s.parents_for("puppies", ["wif", "dog"])
    # Both should be identical due to normalization & memo
    assert a[0]["parent"] == b[0]["parent"]
