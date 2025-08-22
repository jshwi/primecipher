# backend/app/backtest_walk.py
from __future__ import annotations

import math
import sqlite3
import time
import statistics
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Query

from .storage import SNAPSHOT_DB_PATH

router = APIRouter(tags=["backtest"])


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(SNAPSHOT_DB_PATH, timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/backtest/walk")
def backtest_walk(
    narrative: Optional[str] = Query(None, description="Filter tracked pairs by narrative"),
    parent: Optional[str] = Query(None, description="Filter tracked pairs by parent symbol"),
    hold: str = Query("h6", description="Hold window: m5|h1|h6|h24"),
    toleranceMin: int = Query(15, ge=1, le=60, description="Time tolerance (minutes) for snapshot alignment"),
    minLiqUsd: float = Query(0.0, ge=0.0, description="Filter by minimum liquidity at exit snapshot"),
) -> Dict[str, Any]:
    """
    Walk-forward backtest using locally stored snapshots:
      - Find entry snapshot around (now - hold), within tolerance.
      - Find exit snapshot around now, within tolerance.
      - Compute return as (price_exit / price_entry - 1).
    """
    hold_map = {"m5": 5*60, "h1": 3600, "h6": 6*3600, "h24": 24*3600}
    hold_s = hold_map.get(hold.lower(), 6*3600)
    tol = toleranceMin * 60
    now = int(time.time())
    t_entry = now - hold_s

    conn = _connect()
    cur = conn.cursor()

    # Choose candidate pairs
    q = "SELECT pair_address, parent, narrative FROM tracked_pairs WHERE 1=1"
    args: List[Any] = []
    if narrative:
        q += " AND narrative = ?"
        args.append(narrative)
    if parent:
        q += " AND parent = ?"
        args.append(parent.upper())
    q += " ORDER BY last_seen DESC LIMIT 2000"
    cur.execute(q, args)
    pairs = cur.fetchall()

    trades: List[Dict[str, Any]] = []
    returns: List[float] = []

    for row in pairs:
        pair = row["pair_address"]

        # Find snapshots closest to entry and exit
        cur.execute("""
            SELECT ts, price_usd, liquidity_usd FROM pair_snapshots
            WHERE pair_address = ?
            ORDER BY ABS(ts - ?) ASC LIMIT 1
        """, (pair, t_entry))
        entry = cur.fetchone()

        cur.execute("""
            SELECT ts, price_usd, liquidity_usd FROM pair_snapshots
            WHERE pair_address = ?
            ORDER BY ABS(ts - ?) ASC LIMIT 1
        """, (pair, now))
        exit_ = cur.fetchone()

        if not entry or not exit_:
            continue
        if abs(entry["ts"] - t_entry) > tol:
            continue
        if abs(exit_["ts"] - now) > tol:
            continue
        p0 = entry["price_usd"]
        p1 = exit_["price_usd"]
        if p0 is None or p1 is None or p0 <= 0:
            continue
        if minLiqUsd and (exit_["liquidity_usd"] or 0.0) < minLiqUsd:
            continue

        ret = (p1 / p0) - 1.0
        t = {
            "pairAddress": pair,
            "parent": row["parent"],
            "narrative": row["narrative"],
            "entryTs": entry["ts"],
            "exitTs": exit_["ts"],
            "entryPrice": p0,
            "exitPrice": p1,
            "exitLiq": exit_["liquidity_usd"],
            "return": ret,
        }
        trades.append(t)
        returns.append(ret)

    n = len(returns)
    summary = {
        "hold": hold.lower(),
        "n_trades": len(trades),
        "n_with_return": n,
        "winrate_gt0": (sum(1 for r in returns if r > 0) / n) if n else None,
        "mean_return": (statistics.fmean(returns) if n else None),
        "median_return": (statistics.median(returns) if n else None),
        "min_return": (min(returns) if n else None),
        "max_return": (max(returns) if n else None),
        "tolerance_min": toleranceMin,
    }
    return {"summary": summary, "trades": trades}

