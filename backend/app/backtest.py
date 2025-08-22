# backend/app/backtest.py
from __future__ import annotations

import asyncio
import statistics
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Query

from .adapters.onchain import make_onchain_adapter
from .config import PROVIDER
from .seeds import load_narrative_seeds

router = APIRouter(tags=["backtest"])


def _get_seed(narrative: str) -> Optional[Dict[str, Any]]:
    seeds = load_narrative_seeds()
    return next((s for s in seeds if s.get("narrative") == narrative), None)


def _seed_parents(narrative: str) -> List[str]:
    seed = _get_seed(narrative)
    if not seed:
        return []
    parents = seed.get("parents") or []
    out: List[str] = []
    for p in parents:
        sym = (p.get("symbol") or "").strip()
        if sym:
            out.append(sym.upper())
    return out


def _seed_parent_cfg(narrative: str, parent_sym: str) -> Dict[str, Any]:
    seed = _get_seed(narrative) or {}
    parents = seed.get("parents") or []
    upper = parent_sym.upper()
    return next((p for p in parents if (p.get("symbol") or "").upper() == upper), {})  # type: ignore[return-value]


def _child_pair(child: Dict[str, Any]) -> Optional[str]:
    m = child.get("matched") or {}
    addr = m.get("pairAddress")
    if isinstance(addr, str) and addr.strip():
        return addr.strip()
    return None


def _window_key(hold: str) -> str:
    h = hold.lower()
    if h in ("m5", "5m"):
        return "m5"
    if h in ("h1", "1h"):
        return "h1"
    if h in ("h6", "6h"):
        return "h6"
    return "h24"


async def _fetch_pair_change(
    client: httpx.AsyncClient, pair_address: str, window_key: str
) -> Optional[float]:
    # Dexscreener returns percent changes; convert to decimal (e.g. 7.0 -> 0.07)
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
    try:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        pair = (data.get("pairs") or [None])[0] or {}
        change = (pair.get("priceChange") or {}).get(window_key)
        return None if change is None else float(change) / 100.0
    except Exception:
        return None


@router.get("/backtest")
async def backtest(
    narrative: str = Query(..., description="Narrative key, e.g. 'dogs'"),
    parent: Optional[str] = Query(None, description="Limit to a single parent symbol (e.g., 'WIF')."),
    hold: str = Query("h6", description="Hold horizon: m5|h1|h6|h24 (Dexscreener priceChange)"),
    liqMinUsd: float = Query(25_000.0, ge=0.0, description="Min liquidity USD filter"),
    vol24hMinUsd: float = Query(0.0, ge=0.0, description="Min 24h volume USD filter"),
    maxAgeHours: Optional[float] = Query(  # ← now optional (no age filter by default)
        None, ge=0.0, description="Max token age (hours). Omit to ignore age."
    ),
    limitPerParent: int = Query(200, ge=1, le=500),
    allowNameMatch: Optional[bool] = Query(None, description="Override seed nameMatchAllowed"),
    applyBlocklist: bool = Query(True, description="Apply seed blocklist to discovered children"),
):
    """
    Lightweight 'hold-only' backtest:
      - Parents come from seeds (or a single `parent` override).
      - For each parent's children, filter by liq/vol/age (age optional).
      - For each child's pair, read Dexscreener priceChange[hold].
      - Summarize decimal returns.

    NOTE: This is a quick signal check; not a historical walk-forward test.
    """
    # Resolve parents
    if parent:
        parents = [parent.upper()]
    else:
        parents = _seed_parents(narrative)
        if not parents:
            raise HTTPException(status_code=400, detail=f"No parents found in seeds for narrative '{narrative}'.")

    adapter = make_onchain_adapter(PROVIDER)
    window = _window_key(hold)

    discovered: List[Dict[str, Any]] = []

    for p in parents:
        cfg = _seed_parent_cfg(narrative, p)
        terms: List[str] = (cfg.get("match") or [p.lower()])
        allow_name = allowNameMatch if allowNameMatch is not None else cfg.get("nameMatchAllowed", True)
        discovery = cfg.get("discovery") or {}
        block = set(cfg.get("block") or []) if applyBlocklist else set()

        # Discover children for this parent (seed-driven)
        kids = adapter.fetch_children_for_parent(
            parent_symbol=p,
            match_terms=terms,
            allow_name_match=allow_name,
            limit=limitPerParent,
            discovery=discovery,
        )

        # Filter + tag parent
        for c in kids:
            sym_up = (c.get("symbol") or "").upper()
            if sym_up in block:
                continue
            if c.get("liquidityUsd", 0.0) < liqMinUsd:
                continue
            if c.get("volume24hUsd", 0.0) < vol24hMinUsd:
                continue
            age = c.get("ageHours")
            if (maxAgeHours is not None) and (age is not None) and (age > maxAgeHours):
                continue
            if not _child_pair(c):
                continue
            c["__parent"] = p
            discovered.append(c)

    # Concurrent fetch of Dexscreener priceChange
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "narrative-heatmap/0.7"}) as client:
        sem = asyncio.Semaphore(16)

        async def task(child: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[float]]:
            async with sem:
                pair = _child_pair(child)
                ret = await _fetch_pair_change(client, pair, window) if pair else None
                return child, ret

        results = await asyncio.gather(*(task(c) for c in discovered))

    trades: List[Dict[str, Any]] = []
    rets: List[float] = []
    for child, ret in results:
        d: Dict[str, Any] = {
            "parent": child.get("__parent"),
            "symbol": child.get("symbol"),
            "pairAddress": _child_pair(child),
            "liq": child.get("liquidityUsd"),
            "vol24h": child.get("volume24hUsd"),
            "ageHours": child.get("ageHours"),
            "return": ret,  # decimal (0.05 => +5%)
        }
        trades.append(d)
        if isinstance(ret, (int, float)):
            rets.append(float(ret))

    n = len(rets)
    summary = {
        "hold": window,
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
            "hold": window,
            "liqMinUsd": liqMinUsd,
            "vol24hMinUsd": vol24hMinUsd,
            "maxAgeHours": maxAgeHours,
            "limitPerParent": limitPerParent,
            "allowNameMatch": allowNameMatch,
            "applyBlocklist": applyBlocklist,
        },
        "summary": summary,
        "trades": trades,
    }

