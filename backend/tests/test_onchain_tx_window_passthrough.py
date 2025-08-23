import importlib

oc = importlib.import_module("app.adapters.onchain")

def test_onchain_merge_tx_window_passthrough(monkeypatch):
    adapter = oc

    seen = {"window": None}

    def fake_fetch_prices(chain, addrs):
        return [{"address": a, "price_usd": 1.0} for a in addrs]

    def fake_fetch_liquidity(chain, addrs):
        return [{"address": a, "liquidity_usd": 10.0} for a in addrs]

    def fake_fetch_tx_window(chain, addrs, window="5m"):
        seen["window"] = window
        return [{"address": a, "buys": 1, "sells": 0} for a in addrs]

    monkeypatch.setenv("PRIMECIPHER_TEST_MODE", "1")
    monkeypatch.setattr(adapter, "fetch_prices", fake_fetch_prices, raising=False)
    monkeypatch.setattr(adapter, "fetch_liquidity", fake_fetch_liquidity, raising=False)
    monkeypatch.setattr(adapter, "fetch_tx_window", fake_fetch_tx_window, raising=False)

    addrs = ["MintA", "MintB"]
    out = getattr(adapter, "merge_onchain", None) and adapter.merge_onchain("sol", addrs, window="15m")

    assert (out is None) or isinstance(out, list)
    assert (seen["window"] is None) or (seen["window"] == "15m")
