import importlib


def test_onchain_helpers_and_match_terms():
    oc = importlib.import_module("app.adapters.onchain")

    # Helper normalization
    assert oc._norm_alnum_upper("SoL-123") == "SOL123"
    assert oc._norm_alnum_upper(None) == ""
    assert oc._norm_alnum_upper("") == ""

    # Age helper returns float hours or None (repo treats ms differently → be tolerant)
    assert oc._age_hours_ms(None) is None
    v = oc._age_hours_ms(60 * 60 * 1000)
    assert isinstance(v, float) and v > 0.0

    # _match_terms_debug is pure string logic; no HTTP involved
    adapter = oc.DexScreenerAdapter(client=None)
    ok, why = adapter._match_terms_debug("WIF", "dog coin", ["dog", "wif"])
    assert ok is True and isinstance(why, dict)
    ok2, why2 = adapter._match_terms_debug("ABC", "something", ["dog"])
    assert ok2 is False and (why2 is None or isinstance(why2, dict))
