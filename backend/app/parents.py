from __future__ import annotations
from typing import List, Dict
from .config import LIQ_SURVIVAL_THRESHOLD_USD

def build_parent_ecosystems(narrative: str, parents: List[str], adapter) -> List[Dict]:
    rows: List[Dict] = []
    for idx, parent in enumerate(parents):
        children = adapter.fetch_children_for_parent(parent, limit=100)
        children_count = len(children)
        survivors = [c for c in children if (c.get('liquidityUsd') or 0) >= LIQ_SURVIVAL_THRESHOLD_USD]
        h24 = round(len(survivors) / children_count, 4) if children_count else 0.0

        top_child = children[0] if children else None
        row = {
            "parent": parent,
            "narrative": narrative,
            "childrenCount": children_count,
            "childrenNew24h": 0,
            "survivalRates": {"h24": h24, "d7": 0.0},
            "liquidityFunnel": {
                "parentLiquidityUsd": 0.0,
                "childrenLiquidityUsd": float(sum(c.get('liquidityUsd') or 0 for c in children)),
            },
            "topChild": {
                "symbol": top_child.get("symbol") if top_child else None,
                "liquidityUsd": top_child.get("liquidityUsd") if top_child else 0.0,
                "volume24hUsd": top_child.get("volume24hUsd") if top_child else 0.0,
                "ageHours": None,
                "holders": top_child.get("holders") if top_child else None,
            },
        }
        rows.append(row)
    return rows
