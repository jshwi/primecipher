from app.compute import compute_heat

def test_compute_heat_basic():
    narratives = [
        {"narrative": "alpha", "signals": {"onchainVolumeUsd": 100.0, "onchainLiquidityUsd": 50.0}},
        {"narrative": "beta",  "signals": {"onchainVolumeUsd": 200.0, "onchainLiquidityUsd": 25.0}},
        {"narrative": "gamma", "signals": {"onchainVolumeUsd": 150.0, "onchainLiquidityUsd": 75.0}},
    ]
    out = compute_heat(narratives)
    assert isinstance(out, list) and len(out) == 3
    for row in out:
        assert "heatScore" in row and isinstance(row["heatScore"], (int, float))
    heats = sorted([r["heatScore"] for r in out], reverse=True)
    assert heats == sorted(heats, reverse=True)
