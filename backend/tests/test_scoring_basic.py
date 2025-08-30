"""Tests for basic scoring functionality."""


def test_scores_present_and_sorted(client, monkeypatch) -> None:
    """Test that scores are present and sorted correctly.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """

    # force a known set: different matches to see ordering by score
    def deterministic(_self, _: str, __: list[str], **_kw):
        return [
            {"parent": "a", "matches": 10},
            {"parent": "b", "matches": 20},
            {"parent": "c", "matches": 30},
            {"parent": "d", "matches": 40},
        ]

    # patch the source that compute_all() actually uses
    import app.parents as parents_mod

    monkeypatch.setattr(
        parents_mod.Source,
        "parents_for",
        deterministic,
        raising=True,
    )

    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    n = list(body["items"].keys())[0]
    items = body["items"][n]
    assert all("score" in x for x in items)
    scores = [x["score"] for x in items]
    assert scores == sorted(scores, reverse=True)


def test_scores_zero_when_all_equal(client, monkeypatch) -> None:
    """Test that scores are zero when all matches are equal.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """

    def same(_self, _: str, __: list[str], **_kw):
        return [{"parent": f"p{i}", "matches": 10} for i in range(5)]

    import app.parents as parents_mod

    monkeypatch.setattr(parents_mod.Source, "parents_for", same, raising=True)

    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    data = r.json()
    n = list(data["items"].keys())[0]
    items = data["items"][n]
    # all should have z=0 (within tolerance)
    assert all(abs(x.get("score", 0.0)) < 1e-9 for x in items)
