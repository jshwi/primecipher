# backend/app/parents.py
from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timezone
from .config import LIQ_SURVIVAL_THRESHOLD_USD

def _age_hours_ms(created_ms: int | None) -> float | None:
    if not created_ms:
        return None
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return max(0.0, (now_ms - int(created_ms)) / 3_600_000.0)

def build_parent_ecosystems(narrative: str, parents: List[dict], adapter) -> List[Dict]:
    rows: List[Dict] = []
    parent_symbols = [p["symbol"] for p in parents if p.get("symbol")]
    parent_metrics = adapter.fetch_token_metrics(parent_symbols) if parent_symbols else {}

    for p in parents:
        symbol = p["symbol"]
        match_terms = p.get("match") or [symbol.lower()]
        children = adapter.fetch_children_for_parent(symbol, match_terms, limit=100)

        # survival = liquidity above threshold
        survivors = [c for c in children if (c.get("liquidityUsd") or 0) >= LIQ_SURVIVAL_THRESHOLD_USD]
        h24_survival = round(len(survivors) / len(children), 4) if children else 0.0

        # new in 24h
        new24 = 0
        for c in children:
            age = _age_hours_ms(c.get("pairCreatedAt"))
            if age is not None and age <= 24.0:
                new24 += 1

        # top child
        top = children[0] if children else None
        top_age = _age_hours_ms((top or {}).get("pairCreatedAt")) if top else None

        rows.append({
            "parent": symbol,
            "narrative": narrative,
            "childrenCount": len(children),
            "childrenNew24h": new24,
            "survivalRates": {"h24": h24_survival, "d7": 0.0},
            "liquidityFunnel": {
                "parentLiquidityUsd": float(parent_metrics.get(symbol, {}).get("liquidityUsd") or 0.0),
                "childrenLiquidityUsd": float(sum(c.get("liquidityUsd") or 0 for c in children)),
            },
            "topChild": {
                "symbol": (top or {}).get("symbol"),
                "liquidityUsd": float((top or {}).get("liquidityUsd") or 0.0),
                "volume24hUsd": float((top or {}).get("volume24hUsd") or 0.0),
                "ageHours": top_age,
                "holders": (top or {}).get("holders"),
            },
        })
    return rows

