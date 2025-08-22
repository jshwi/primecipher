# backend/app/backtest_walk.py
from __future__ import annotations

import sqlite3
import time
import statistics
from typing import Any, Dict, List, Optional

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
    maxEntryAgeHours: Optional[float] = Query(  # NEW
        None,
        ge=0.0,
        description="Only include trades where (entry time - first_seen) <= this many hours. Omit to disable.",
    ),
) -> Dict[str, Any]:
    """
    Walk-forward backtest using locally stored snapshots:
      - Entry snapshot near (now - hold), within tolerance.
      - Exit snapshot near now, within tolerance.
      - Optional 'enter-on-new' via maxEntryAgeHours.
      - Return = (price_exit / price_entry - 1).

    Adds a helpful `summary.note` when no trades match and `diagnostics` counters.
    """
    hold_map = {"m5": 5 * 60, "h1": 3600, "h6": 6 * 3600, "h24": 24 * 3600}
    hold_s = hold_map.get(hold.lower(), 6 * 3600)
    tol_s = toleranceMin * 60
    now = int(time.time())
    t_entry = now - hold_s

    conn = _connect()
    cur = conn.cursor()

    # Choose candidate pairs (include first_seen for entry-age filter)
    q = "SELECT pair_address, parent, narrative, first_seen FROM tracked_pairs WHERE 1=1"
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

    # Diagnostics
    diag_total_pairs = len(pairs)
    diag_entry_found = 0
    diag_exit_found = 0
    diag_entry_within_tol = 0
    diag_exit_within_tol = 0
    diag_priced_pairs = 0
    diag_liq_ok = 0
    diag_entry_age_kept = 0  # NEW

    trades: List[Dict[str, Any]] = []
    returns: List[float] = []

    for row in pairs:
        pair = row["pair_address"]
        first_seen = row["first_seen"]  # epoch seconds

        # Entry snapshot (nearest to target entry time)
        cur.execute(
            """
            SELECT ts, price_usd, liquidity_usd FROM pair_snapshots
            WHERE pair_address = ?
            ORDER BY ABS(ts - ?) ASC LIMIT 1
            """,
            (pair, t_entry),
        )
        entry = cur.fetchone()
        if entry:
            diag_entry_found += 1
        else:
            continue

        # Exit snapshot (nearest to now)
        cur.execute(
            """
            SELECT ts, price_usd, liquidity_usd FROM pair_snapshots
            WHERE pair_address = ?
            ORDER BY ABS(ts - ?) ASC LIMIT 1
            """,
            (pair, now),
        )
        exit_ = cur.fetchone()
        if exit_:
            diag_exit_found += 1
        else:
            continue

        if abs(entry["ts"] - t_entry) <= tol_s:
            diag_entry_within_tol += 1
        else:
            continue

        if abs(exit_["ts"] - now) <= tol_s:
            diag_exit_within_tol += 1
        else:
            continue

        # NEW: enter-on-new filter (age at entry)
        entry_age_hours: Optional[float] = None
        if isinstance(first_seen, int):
            entry_age_hours = max(0.0, (t_entry - first_seen) / 3600.0)
            if maxEntryAgeHours is not None and entry_age_hours > maxEntryAgeHours:
                continue
            diag_entry_age_kept += 1

        p0 = entry["price_usd"]
        p1 = exit_["price_usd"]
        if p0 is None or p1 is None or p0 <= 0:
            continue
        diag_priced_pairs += 1

        if minLiqUsd and (exit_["liquidity_usd"] or 0.0) < minLiqUsd:
            continue
        diag_liq_ok += 1

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
            "entryAgeHours": entry_age_hours,  # NEW
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
        "note": (
            "No matching snapshots; ensure at least two timepoints spanning the hold window, "
            "or use the synthetic_backfill tool to seed entries."
            if len(trades) == 0
            else None
        ),
    }

    diagnostics = {
        "pairs_considered": diag_total_pairs,
        "entry_target_ts": t_entry,
        "exit_target_ts": now,
        "tolerance_sec": tol_s,
        "entry_found_any": diag_entry_found,
        "exit_found_any": diag_exit_found,
        "entry_within_tolerance": diag_entry_within_tol,
        "exit_within_tolerance": diag_exit_within_tol,
        "priced_pairs": diag_priced_pairs,
        "liq_ok_pairs": diag_liq_ok,
        "entry_age_kept": diag_entry_age_kept,  # NEW
    }

    return {"summary": summary, "diagnostics": diagnostics, "trades": trades}

