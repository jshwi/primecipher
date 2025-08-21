# backend/scripts/generate_stub_data.py
from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"            # generated snapshots (gitignored)
DISC_DIR = DATA_DIR / "discovered"  # placeholders / future discoveries
SEEDS_DIR = ROOT / "seeds"          # small, assumed subsets (committed)

DATA_DIR.mkdir(parents=True, exist_ok=True)
DISC_DIR.mkdir(parents=True, exist_ok=True)
SEEDS_DIR.mkdir(parents=True, exist_ok=True)

SEED_FILE = SEEDS_DIR / "narratives.seed.json"

# ---- helpers ---------------------------------------------------------------

def load_seed_narratives() -> list[dict]:
    """
    Load tiny seed set from /seeds/narratives.seed.json.
    If missing, fall back to a minimal default.
    """
    if SEED_FILE.exists():
        return json.loads(SEED_FILE.read_text(encoding="utf-8"))
    # minimal fallback seed
    return [
        {"narrative": "dogs", "keywords": ["wif", "dog", "moodeng"], "parents": ["WIF", "MOODENG"]},
        {"narrative": "ai", "keywords": ["ai", "gpt", "tao", "fet"], "parents": ["FET", "TAO"]},
    ]


def mk_narrative_payload(seed: dict, window: str = "24h") -> dict:
    """
    Produce a deterministic stub payload for a narrative using seed info.
    Replace these constants with real adapter outputs in Step 2.
    """
    base_vol = 1_000_000
    base_liq = 500_000
    ct_mentions = 10_000

    # light deterministic jitter based on name length so cards don't look identical
    j = len(seed["narrative"])
    vol = base_vol + j * 12_345
    liq = base_liq + j * 7_890
    ct = ct_mentions + j * 321

    heat = min(100.0, 60.0 + j * 2.7)  # arbitrary, just to vary visuals

    return {
        "narrative": seed["narrative"],
        "heatScore": round(heat, 1),
        "window": window,
        "signals": {
            "onchainVolumeUsd": float(vol),
            "onchainLiquidityUsd": float(liq),
            "ctMentions": int(ct),
        },
        "parents": seed.get("parents", []),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }


def mk_parent_ecosystem_stub(parent: str, narrative: str, k: int) -> dict:
    """
    Deterministic parent ecosystem stub. 'k' is an index to vary numbers.
    """
    children_count = 50 + k * 13
    new_24h = max(0, min(children_count, 10 + k * 3))
    surv_h24 = max(0.005, min(0.15, 0.01 * (k + 1)))
    surv_d7 = max(0.003, min(0.08, 0.006 * (k + 1)))

    parent_liq = 10_000_000 + k * 1_250_000
    children_liq = 350_000 + k * 140_000
    top_child_vol = 150_000 + k * 95_000
    top_child_liq = 40_000 + k * 22_000
    holders = 600 + k * 190

    return {
        "parent": parent,
        "narrative": narrative,
        "childrenCount": children_count,
        "childrenNew24h": new_24h,
        "survivalRates": {"h24": round(surv_h24, 4), "d7": round(surv_d7, 4)},
        "liquidityFunnel": {
            "parentLiquidityUsd": parent_liq,
            "childrenLiquidityUsd": children_liq,
        },
        "topChild": {
            "symbol": f"{parent}Child{k+1}",
            "liquidityUsd": top_child_liq,
            "volume24hUsd": top_child_vol,
            "ageHours": 6 + k * 2,
            "holders": holders,
        },
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }


# ---- main ------------------------------------------------------------------

def main() -> None:
    seeds = load_seed_narratives()

    # 1) Write narratives snapshot (single file)
    narratives_payload = [mk_narrative_payload(s, "24h") for s in seeds]
    (DATA_DIR / "narratives-24h.json").write_text(
        json.dumps(narratives_payload, indent=2), encoding="utf-8"
    )

    # 2) For each narrative, write a parents snapshot file:
    #    data/parents-<narrative>-24h.json
    for s in seeds:
        narrative = s["narrative"]
        parents = s.get("parents", []) or []
        if not parents:
            # still emit an empty array so the UI doesn't 404
            (DATA_DIR / f"parents-{narrative}-24h.json").write_text("[]", encoding="utf-8")
            continue

        rows = [mk_parent_ecosystem_stub(p, narrative, idx) for idx, p in enumerate(parents)]
        (DATA_DIR / f"parents-{narrative}-24h.json").write_text(
            json.dumps(rows, indent=2), encoding="utf-8"
        )

    # 3) Discovered candidates placeholder (used later by live adapters)
    (DISC_DIR / "parents-candidates-24h.json").write_text("[]", encoding="utf-8")

    print("Wrote:")
    print(f"  - {DATA_DIR / 'narratives-24h.json'}")
    for s in seeds:
        print(f"  - {DATA_DIR / f'parents-{s['narrative']}-24h.json'}")
    print(f"  - {DISC_DIR / 'parents-candidates-24h.json'}")


if __name__ == "__main__":
    main()

