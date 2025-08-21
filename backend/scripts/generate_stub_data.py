from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

narratives = [
    {
        "narrative": "dogs",
        "heatScore": 83.2,
        "window": "24h",
        "signals": {
            "onchainVolumeUsd": 1_240_032.5,
            "onchainLiquidityUsd": 532_881.0,
            "ctMentions": 18_230,
        },
        "parents": ["WIF", "MOODENG"],
    },
    {
        "narrative": "ai",
        "heatScore": 61.5,
        "window": "24h",
        "signals": {
            "onchainVolumeUsd": 820_400.0,
            "onchainLiquidityUsd": 410_200.0,
            "ctMentions": 9_410,
        },
        "parents": ["FET", "TAO"],
    },
    {
        "narrative": "politics",
        "heatScore": 38.9,
        "window": "24h",
        "signals": {
            "onchainVolumeUsd": 210_000.0,
            "onchainLiquidityUsd": 95_000.0,
            "ctMentions": 3_120,
        },
        "parents": ["TRUMP", "BIDEN"],
    },
]

parents_dogs = [
    {
        "parent": "WIF",
        "narrative": "dogs",
        "childrenCount": 240,
        "childrenNew24h": 61,
        "survivalRates": {"h24": 0.012, "d7": 0.006},
        "liquidityFunnel": {
            "parentLiquidityUsd": 26_500_000,
            "childrenLiquidityUsd": 1_120_000,
        },
        "topChild": {
            "symbol": "MoodengWifHat",
            "liquidityUsd": 86_000,
            "volume24hUsd": 421_000,
            "ageHours": 7.5,
            "holders": 1_831,
        },
    },
    {
        "parent": "MOODENG",
        "narrative": "dogs",
        "childrenCount": 90,
        "childrenNew24h": 19,
        "survivalRates": {"h24": 0.089, "d7": 0.031},
        "liquidityFunnel": {
            "parentLiquidityUsd": 12_400_000,
            "childrenLiquidityUsd": 980_000,
        },
        "topChild": {
            "symbol": "BabyMoodeng",
            "liquidityUsd": 64_000,
            "volume24hUsd": 195_000,
            "ageHours": 11.0,
            "holders": 990,
        },
    },
]

(DATA / "narratives-24h.json").write_text(json.dumps(narratives, indent=2), encoding="utf-8")
(DATA / "parents-dogs-24h.json").write_text(json.dumps(parents_dogs, indent=2), encoding="utf-8")

print("Wrote data/narratives-24h.json and data/parents-dogs-24h.json")
