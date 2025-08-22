# backend/app/backtest.py
from __future__ import annotations

import asyncio
import statistics
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Query

from .adapters.onchain import make_onchain_adapter
from .config import PROVIDER

router = APIRouter(tags=["backtest"])


def _child_has_pair(child: Dict[str, Any]) -> Optional[str]:
    m = child.get("matched") or {}
    addr = m.get("pairAddress")
    if isinstance(addr, str) and addr.strip():
        return addr.strip()
    return None


def _choose_window_key(hold: str) -> str:
    # normalize to Dexscreener keys
    hold = hold.lower()
    if hold in ("m5", "5m"):
        return "m5"
    if hold in ("h1", "1h"):
        return "h1"
    if hold in ("h6", "6h"):
        return "h6"
    return "h24"  # default


async def _fetch_pair_change(
    client: httpx.AsyncClient, pair_address: str, window_key: str
) -> Optional[float]:
    # Dexscreener latest pair endpoint shape:
    # { "pairs": [ { "priceChange": { "m5": 1.2, "h1": -3.4, "h6": 5.6, "h24": 12.3 }, ... } ] }
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
    try:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        pair = (data.get("pairs") or [None])[0] or {}
        change = (pair.get("priceChange") or {}).get(window_key)
        if change is None:
            return None
        # Dexscreener returns % change; convert to decimal return (e.g., 5.0 -> 0.05)
        return float(change) / 100.0
    except Exception:
        return None


@router.get("/backtest")
async def backtest(
    narrative: str = Query(..., description="Narrative key, e.g. 'dogs'"),
    parent: Optional[str] = Query(
        None, description="Limit to a single parent symbol (e.g. 'WIF')."
    ),
    hold: str = Query(
        "h6", description="Hold horizon: m5|h1|h6|h24 (uses Dexscreener priceChange fields)"
    ),
    liqMinUsd: float = Query(25_000.0, ge=0.0, description="Min liquidity USD filter"),
    vol24hMinUsd: float = Query(0.0, ge=0.0, description="Min 24h volume USD filter"),
    maxAgeHours: float = Query(14 * 24.0, ge=0.0, description="Max token age (hours)"),
    limitPerParent: int = Query(200, ge=1, le=500),
    allowNameMatch: Optional[bool] = Query(
        None, description="Override seed allowNameMatch if needed"
    ),
):
    """
    Lightweight 'hold-only' backtest:
    - Discover children for the narrative (optionally one parent).
    - Filter by liq/vol/age.
    - For each child's pair, read Dexscreener `priceChange[hold]`.
    - Summarize returns (decimal) as if entered exactly `hold` ago and exited now.

    NOTE: This is NOT a full historical backtest; it uses Dexscreener point-in-time deltas.
    Next step is snapshotting OHLC over time for true walk-forward testing.
    """
    adapter = make_onchain_adapter(PROVIDER)
    window_key = _choose_window_key(hold)

    # Choose parents to evaluate
    parents: List[str]
    if parent:
        parents = [parent.upper()]
    else:
        # Reuse your "parents list" endpoint via adapter: ask for narrative parents
        # We approximate by reading discovery with wide terms = narrative key itself.
        # If your project already exposes parents for a narrative, replace this with that call.
        parents = adapter.list_parents_for_narrative(narrative)  # type: ignore[attr-defined]

    # Discover & filter children
    discovered: List[Dict[str, Any]] = []
    for p in parents:
        kids = adapter.fetch_children_for_parent(
            parent_symbol=p,
            match_terms=[p.lower()],  # seed matching is applied inside adapter
            allow_name_match=True if allowNameMatch is None else allowNameMatch,
            limit=limitPerParent,
            discovery={},  # keep defaults; adjust if needed
        )
        for c in kids:
            if c.get("liquidityUsd", 0.0) < liqMinUsd:
                continue
            if c.get("volume24hUsd", 0.0) < vol24hMinUsd:
                continue
            age = c.get("ageHours")
            if age is not None and age > maxAgeHours:
                continue
            if not _child_has_pair(c):
                continue
            c["__parent"] = p
            discovered.append(c)

    # Concurrently fetch per-pair price change
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "narrative-heatmap/0.5"}) as client:
        sem = asyncio.Semaphore(16)

        async def task(child: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[float]]:
            async with sem:
                pair = _child_has_pair(child)
                change = await _fetch_pair_change(client, pair, window_key) if pair else None
                return child, change

        results = await asyncio.gather(*(task(c) for c in discovered))

    trades: List[Dict[str, Any]] = []
    rets: List[float] = []
    for child, ret in results:
        pair = _child_has_pair(child)
        d: Dict[str, Any] = {
            "parent": child.get("__parent"),
            "symbol": child.get("symbol"),
            "pairAddress": pair,
            "liq": child.get("liquidityUsd"),
            "vol24h": child.get("volume24hUsd"),
            "ageHours": child.get("ageHours"),
            "return": ret,  # decimal (0.05 = +5%)
        }
        trades.append(d)
        if isinstance(ret, (int, float)):
            rets.append(float(ret))

    n = len(rets)
    summary = {
        "hold": window_key,
        "n_trades": len(trades),
        "n_with_return": n,
        "winrate_gt0": (sum(1 for r in rets if r > 0) / n) if n else None,
        "mean_return": (statistics.fmean(rets) if n else None),
        "median_return": (statistics.median(rets) if n else None),
        "min_return": (min(rets) if n else None),
        "max_return": (max(rets) if n else None),
    }

    return {
        "params": {
            "narrative": narrative,
            "parents": parents,
            "hold": window_key,
            "liqMinUsd": liqMinUsd,
            "vol24hMinUsd": vol24hMinUsd,
            "maxAgeHours": maxAgeHours,
            "limitPerParent": limitPerParent,
            "allowNameMatch": allowNameMatch,
        },
        "summary": summary,
        "trades": trades,
    }

