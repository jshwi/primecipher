from __future__ import annotations
from typing import List, Dict
from .config import LIQ_SURVIVAL_THRESHOLD_USD

def build_parent_ecosystems(narrative: str, parents: List[str], adapter) -> List[Dict]:
    rows: List[Dict] = []
    # also fetch parent metrics to populate parentLiquidityUsd
    parent_metrics = adapter.fetch_token_metrics(parents) if parents else {}

    for parent in parents:
        children = adapter.fetch_children_for_parent(parent, limit=100)
        children_count = len(children)
        survivors = [c for c in children if (c.get('liquidityUsd') or 0) >= LIQ_SURVIVAL_THRESHOLD_USD]
        h24 = round(len(survivors) / children_count, 4) if children_count else 0.0

        top_child = children[0] if children else None
        rows.append({
            "parent": parent,
            "narrative": narrative,
            "childrenCount": children_count,
            "childrenNew24h": 0,  # TBD when we parse pairCreatedAt
            "survivalRates": {"h24": h24, "d7": 0.0},
            "liquidityFunnel": {
                "parentLiquidityUsd": float(parent_metrics.get(parent, {}).get("liquidityUsd") or 0.0),
                "childrenLiquidityUsd": float(sum(c.get('liquidityUsd') or 0 for c in children)),
            },
            "topChild": {
                "symbol": (top_child or {}).get("symbol"),
                "liquidityUsd": float((top_child or {}).get("liquidityUsd") or 0.0),
                "volume24hUsd": float((top_child or {}).get("volume24hUsd") or 0.0),
                "ageHours": None,
                "holders": (top_child or {}).get("holders"),
            },
        })
    return rows

