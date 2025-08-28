from app.adapters.source import _apply_seed_semantics

def test_allow_name_match_false_keeps_when_other_terms_present():
    # name "dogs" is present, but so is another term → should be KEPT
    items = [
        {"parent": "dogs",            "matches": 50},  # should be dropped (name-only)
        {"parent": "dogs wif",        "matches": 60},  # should be kept (name + another term)
        {"parent": "blocked token",   "matches": 99},  # should be dropped by blocklist
    ]
    out = _apply_seed_semantics(
        narrative="dogs",
        terms=["dogs", "wif", "shib"],
        allow_name_match=False,          # disallow name-only matches
        block=["blocked"],
        items=items,
        require_all_terms=False,         # not enforcing all-terms here
    )
    # kept row should be the "dogs wif" one, sorted/sliced to top 3 (only 1 remains)
    assert out == [{"parent": "dogs wif", "matches": 60}]

def test_require_all_terms_positive_branch_keeps_item_with_all_terms():
    # Only the third item has ALL terms → ensures the 'all(...)' keep branch is covered
    items = [
        {"parent": "dogs",               "matches": 10},                 # missing "wif"
        {"parent": "wif shib",           "matches": 20},                 # missing "dogs"
        {"parent": "dogs wif shib",      "matches": 30},                 # has all three → keep
    ]
    out = _apply_seed_semantics(
        narrative="dogs",
        terms=["dogs", "wif", "shib"],
        allow_name_match=True,
        block=[],
        items=items,
        require_all_terms=True,          # enforce all-terms present
    )
    assert out == [{"parent": "dogs wif shib", "matches": 30}]
