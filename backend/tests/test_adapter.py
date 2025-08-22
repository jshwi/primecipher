import time
import types
import pytest

from backend.app.adapters.onchain import DexScreenerAdapter

NOW_MS = int(time.time() * 1000)

def pair(**kw):
    """Minimal DexScreener pair stub on Solana/Raydium."""
    base = kw.pop("baseToken", {})
    return {
        "chainId": "solana",
        "dexId": kw.pop("dexId", "raydium"),
        "baseToken": {
            "address": base.get("address", "ADDR"),
            "symbol": base.get("symbol", "SYM"),
            "name": base.get("name", "NAME"),
        },
        "pairAddress": kw.pop("pairAddress", "PAIR"),
        "liquidity": {"usd": kw.pop("liq_usd", 1_000)},
        "volume": {"h24": kw.pop("vol_usd", 100)},
        "pairCreatedAt": kw.pop("pairCreatedAt", NOW_MS - 6 * 3600 * 1000),
        **kw,
    }

def make_adapter_with_pairs(pairs_by_query: dict[str, list[dict]]):
    """Adapter whose _search_pairs returns our stubs."""
    ad = DexScreenerAdapter()
    def _search_pairs(self, q: str):
        return pairs_by_query.get(q, [])
    ad._search_pairs = types.MethodType(_search_pairs, ad)
    return ad

def test_children_excludes_parent_and_normalizes_symbol():
    """
    Parent=WIF, ensure child list:
    - excludes self when base symbol is '$WIF' (normalization),
    - includes legit symbol-hit like 'DOGWIF'.
    """
    pairs = {
        # queries will include 'WIF' (default term)
        "WIF": [
            # self (must be excluded)
            pair(baseToken={"symbol": "$WIF", "name": "Dogwifhat"}, pairAddress="PAIR_PARENT", vol_usd=9999, liq_usd=1_000_000),
            # legit child (symbol contains 'wif')
            pair(baseToken={"symbol": "DOGWIF", "name": "Dog Wif Something"}, pairAddress="PAIR_CHILD", vol_usd=200, liq_usd=5_000),
        ],
    }
    ad = make_adapter_with_pairs(pairs)
    children = ad.fetch_children_for_parent("WIF", match_terms=["wif"], allow_name_match=False, limit=10)
    symbols = [c["symbol"] for c in children]
    assert "DOGWIF" in symbols
    assert not any(s.upper().replace("$", "") == "WIF" for s in symbols), "parent token must not appear as child"

def test_nameMatchAllowed_flag_controls_name_only_matches():
    """
    When allow_name_match=False, a token matching only by NAME (term len>=5) must be excluded.
    When True, it can be included.
    """
    # Construct a pair whose SYMBOL doesn't include 'wifhat', but NAME does.
    pairs = {
        "wifhat": [
            pair(baseToken={"symbol": "SANTA", "name": "dogwifhat tribute"}, pairAddress="PAIR_NAME_ONLY", vol_usd=150, liq_usd=2_000),
        ],
    }
    ad = make_adapter_with_pairs(pairs)

    # Disallow name-only
    children_no_name = ad.fetch_children_for_parent("WIF", match_terms=["wifhat"], allow_name_match=False, limit=10)
    assert all(c["symbol"] != "SANTA" for c in children_no_name)

    # Allow name-only
    children_with_name = ad.fetch_children_for_parent("WIF", match_terms=["wifhat"], allow_name_match=True, limit=10)
    assert any(c["symbol"] == "SANTA" for c in children_with_name)

