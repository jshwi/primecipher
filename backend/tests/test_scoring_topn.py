from typing import List

def test_topn_cap_100(client, monkeypatch):
    def many(_self, narrative: str, terms: List[str], **_kw):
        # 150 items with increasing matches
        return [{"parent": f"p{i:03d}", "matches": i} for i in range(150)]
    import app.parents as parents_mod
    monkeypatch.setattr(parents_mod.Source, "parents_for", many, raising=True)

    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    data = r.json()
    n = list(data["items"].keys())[0]
    items = data["items"][n]
    assert len(items) == 100  # capped at TOP_N
    scores = [x["score"] for x in items]
    assert scores == sorted(scores, reverse=True)
