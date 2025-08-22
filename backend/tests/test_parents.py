from backend.app.parents import build_parent_ecosystems

class FakeAdapter:
    def fetch_parent_metrics(self, parents):
        # return stable parent liq to avoid None issues
        return {p["symbol"]: {"liquidityUsd": 10000, "volume24hUsd": 5000} for p in parents}

    def fetch_children_for_parent(self, parent_symbol, match_terms, allow_name_match=True, limit=100, discovery=None):
        # Return one blocked and one allowed child
        return [
            {"symbol": "WITH", "liquidityUsd": 3000, "volume24hUsd": 1000, "ageHours": 10},
            {"symbol": "DOGWIF", "liquidityUsd": 4000, "volume24hUsd": 1200, "ageHours": 12},
        ]

def test_blocklist_filters_children_in_parents():
    adapter = FakeAdapter()
    p = {
        "symbol": "WIF",
        "match": ["wif"],
        "block": ["WITH"],              # block this child
        "nameMatchAllowed": False,
        "discovery": {},                # no overrides
    }
    rows = build_parent_ecosystems("dogs", [p], adapter)
    assert len(rows) == 1
    row = rows[0]
    assert row["parent"] == "WIF"
    assert row["childrenCount"] == 1, "blocked child should be removed"
    assert row["topChild"]["symbol"] == "DOGWIF"
    # survival rate computed over remaining children
    assert 0.0 <= row["survivalRates"]["h24"] <= 1.0

