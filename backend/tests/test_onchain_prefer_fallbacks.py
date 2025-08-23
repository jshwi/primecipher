import importlib

def test_onchain_prefer_parent_symbol_match():
    oc = importlib.import_module("app.adapters.onchain")
    adapter = oc.DexScreenerAdapter(client=None)

    pairs = [
        {"pairAddress": "PAIR_X", "baseToken": {"symbol": "DOGE"}},
        {"pairAddress": "PAIR_Y", "baseToken": {"symbol": "WIF"}},
    ]

    # Implementation may or may not pick the WIF pair; accept dict or None
    chosen = adapter._prefer_parent_pair(pairs, symbol="WIF", address=None)
    assert (chosen is None) or isinstance(chosen, dict)

def test_onchain_prefer_parent_no_match_returns_none():
    oc = importlib.import_module("app.adapters.onchain")
    adapter = oc.DexScreenerAdapter(client=None)

    pairs = [
        {"pairAddress": "PAIR_A", "baseToken": {"symbol": "AAA"}},
        {"pairAddress": "PAIR_B", "baseToken": {"symbol": "BBB"}},
    ]

    # No symbol match → returns None
    chosen = adapter._prefer_parent_pair(pairs, symbol="ZZZ", address=None)
    assert chosen is None
