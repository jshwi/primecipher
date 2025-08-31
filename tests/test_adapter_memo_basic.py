"""Tests for basic adapter memoization functionality."""


def test_memo_across_narratives_same_terms(monkeypatch) -> None:
    """Test that memoization works across narratives with same terms.

    :param monkeypatch: Pytest fixture for patching.
    """
    # count calls into the raw producer
    calls = {"n": 0}

    import backend.adapters.source as src

    def fake_det(_, __):
        calls["n"] += 1
        return [{"parent": "X", "matches": 10}, {"parent": "Y", "matches": 9}]

    # force 'test' provider (deterministic) and patch its raw producer
    monkeypatch.setenv("SOURCE_MODE", "test")
    # ensure fresh module constants
    import importlib

    importlib.reload(src)
    monkeypatch.setattr(src, "_deterministic_items", fake_det, raising=True)

    s = src.Source()  # uses provider 'test'
    # two different narratives, same terms -> one underlying fetch
    s.parents_for("dogs", ["Dog", "wif"])
    s.parents_for("puppies", ["wif", "dog"])  # different order/case

    assert calls["n"] == 1  # memo hit on second call
