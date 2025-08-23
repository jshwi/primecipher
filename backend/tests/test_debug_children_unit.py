def test_debug_children_seeds_overrides_and_pagination(monkeypatch):
    import app.debug as dbg

    # 1) Seed data so _find_seed_parent() resolves and provides flags/blocklist/discovery
    seeds_data = [
        {
            "narrative": "ai",
            "parents": [
                {
                    "symbol": "FET",
                    "match": ["ai"],               # forces terms from seed (not default)
                    "nameMatchAllowed": False,     # will be overridden below
                    "block": ["BLOCKED"],          # used when applyBlocklist=True
                    "discovery": {"dexIds": ["raydium"], "volMinUsd": 123.0},
                }
            ],
        }
    ]
    monkeypatch.setattr(dbg, "load_narrative_seeds", lambda: seeds_data, raising=False)

    # 2) Fake on-chain adapter to avoid I/O; return a superset including a blocked symbol
    captured = {}
    class FakeAdapter:
        def fetch_children_for_parent(self, *, parent_symbol, match_terms, allow_name_match, limit, discovery):
            captured.update(
                parent_symbol=parent_symbol,
                match_terms=match_terms,
                allow_name_match=allow_name_match,
                limit=limit,
                discovery=discovery,
            )
            return [
                {"symbol": "OK1"},
                {"symbol": "BLOCKED"},
                {"symbol": "OK2"},
                {"symbol": "OK3"},
            ]

    monkeypatch.setattr(dbg, "make_onchain_adapter", lambda _provider: FakeAdapter(), raising=False)

    # 3) Call the function with overrides that hit all the branches:
    #    - applyBlocklist=True -> filters out "BLOCKED"
    #    - allowNameMatch overrides seed's False -> True
    #    - discovery overrides dexIds, volMinUsd, liqMinUsd, maxAgeHours
    #    - pagination after filtering: offset=1, limit=2
    out = dbg.debug_children(
        parent="FET",
        narrative="ai",
        applyBlocklist=True,
        allowNameMatch=True,
        dexIds="raydium, orca",
        volMinUsd=50,
        liqMinUsd=10,
        maxAgeHours=24,
        limit=2,
        offset=1,
    )

    # 4) Assertions on adapter call
    assert captured["parent_symbol"] == "FET"
    assert captured["match_terms"] == ["ai"]
    assert captured["allow_name_match"] is True
    # effective_limit should be offset+limit (<=500): here max(2, 3) = 3
    assert captured["limit"] == 3
    assert captured["discovery"]["dexIds"] == ["raydium", "orca"]
    assert captured["discovery"]["volMinUsd"] == 50.0
    assert captured["discovery"]["liqMinUsd"] == 10.0
    assert captured["discovery"]["maxAgeHours"] == 24.0

    # 5) Output structure + blocklist + pagination after filtering
    assert out["resolved"]["parent"] == "FET"
    assert out["resolved"]["narrative"] == "ai"
    assert out["resolved"]["allowNameMatch"] is True
    assert out["resolved"]["discovery"] == {
        "dexIds": ["raydium", "orca"],
        "volMinUsd": 50.0,
        "liqMinUsd": 10.0,
        "maxAgeHours": 24.0,
    }

    # children returned should be filtered (BLOCKED removed) then paginated: offset=1, limit=2
    # filtered list would be ["OK1","OK2","OK3"] ⇒ page is ["OK2","OK3"]
    assert [c["symbol"] for c in out["children"]] == ["OK2", "OK3"]

    assert out["counts"]["total"] == 4          # pre-blocklist
    assert out["counts"]["returned"] == 2       # after blocklist + pagination
    assert out["counts"]["offset"] == 1
    assert out["counts"]["limit"] == 2
