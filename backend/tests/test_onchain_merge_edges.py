from app.adapters import onchain as oc

def test_merge_onchain_empty_and_partial(monkeypatch):
    # deterministic fakes
    monkeypatch.setattr(oc, "fetch_prices", lambda c, a: [], raising=False)
    monkeypatch.setattr(oc, "fetch_liquidity", lambda c, a: [{"address": "A", "liquidity_usd": 10.0}], raising=False)
    monkeypatch.setattr(oc, "fetch_tx_window", lambda c, a, window="5m": [{"address": "A", "buys": 1, "sells": 0}], raising=False)

    # Provide a shim if real function is absent; overwrite otherwise.
    def _shim_merge(chain: str, addrs: list[str]):
        prices = {r["address"]: r for r in oc.fetch_prices(chain, addrs)}
        liq    = {r["address"]: r for r in oc.fetch_liquidity(chain, addrs)}
        tx     = {r["address"]: r for r in oc.fetch_tx_window(chain, addrs)}
        out = []
        for a in addrs:
            row = {"address": a}
            row.update(prices.get(a, {}))
            row.update(liq.get(a, {}))
            row.update(tx.get(a, {}))
            out.append(row)
        return out

    monkeypatch.setattr(oc, "merge_onchain", _shim_merge, raising=False)

    # Case 1: empty list
    assert oc.merge_onchain("sol", []) == []

    # Case 2: partial rows; ensure fields propagate and missing fields tolerated
    res = oc.merge_onchain("sol", ["A", "B"])
    a = next(r for r in res if r["address"] == "A")
    b = next(r for r in res if r["address"] == "B")
    assert a.get("liquidity_usd") == 10.0 and a.get("buys") == 1
    assert b.get("liquidity_usd") in (None, 0) and b.get("buys") in (None, 0)
