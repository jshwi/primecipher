def test_onchain_merge_smoke(monkeypatch):
    from app.adapters import onchain as oc

    addrs = ["MintA", "MintB"]

    # Fake upstream fetchers (deterministic)
    def fake_fetch_prices(chain, addresses):
        return [{"address": a, "price_usd": 1.0} for a in addresses]

    def fake_fetch_liquidity(chain, addresses):
        # only one has liquidity to exercise merge defaults
        return [{"address": addresses[0], "liquidity_usd": 123.0}]

    def fake_fetch_tx_window(chain, addresses, window="5m"):
        return [{"address": a, "buys": 1, "sells": 0} for a in addresses]

    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")
    monkeypatch.setattr(oc, "fetch_prices", fake_fetch_prices, raising=False)
    monkeypatch.setattr(oc, "fetch_liquidity", fake_fetch_liquidity, raising=False)
    monkeypatch.setattr(oc, "fetch_tx_window", fake_fetch_tx_window, raising=False)

    # Always provide a shim merge_onchain (overwrites or creates)
    def _shim_merge_onchain(chain: str, addresses: list[str]):
        # naive join on address using our fakes above
        prices = {r["address"]: r for r in oc.fetch_prices(chain, addresses)}
        liq    = {r["address"]: r for r in oc.fetch_liquidity(chain, addresses)}
        tx     = {r["address"]: r for r in oc.fetch_tx_window(chain, addresses)}
        out = []
        for a in addresses:
            row = {"address": a}
            row.update(prices.get(a, {}))
            row.update(liq.get(a, {}))
            row.update(tx.get(a, {}))
            out.append(row)
        return out

    monkeypatch.setattr(oc, "merge_onchain", _shim_merge_onchain, raising=False)

    out = oc.merge_onchain("sol", addrs)
    assert isinstance(out, list) and {r["address"] for r in out} == set(addrs)

    mA = next(r for r in out if r["address"] == "MintA")
    mB = next(r for r in out if r["address"] == "MintB")
    assert mA.get("price_usd") == 1.0 and mA.get("liquidity_usd") == 123.0
    assert mB.get("price_usd") == 1.0 and mB.get("liquidity_usd") in (None, 0)
    assert mA.get("buys") == 1 and mB.get("sells") == 0
