"""Tests for top-N scoring functionality."""


def test_topn_cap_100(client, monkeypatch) -> None:
    """Test that top-N scoring caps results at 100 items.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """

    def many(_self, _: str, __: list[str], **_kw):
        # 150 items with increasing matches
        return [{"parent": f"p{i:03d}", "matches": i} for i in range(150)]

    import backend.parents as parents_mod

    monkeypatch.setattr(parents_mod.Source, "parents_for", many, raising=True)

    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    data = r.json()
    n = list(data["items"].keys())[0]
    items = data["items"][n]
    assert len(items) == 100  # capped at TOP_N
    scores = [x["score"] for x in items]
    assert scores == sorted(scores, reverse=True)
