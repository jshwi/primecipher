# backend/app/backtest_walk.py
from __future__ import annotations

import sqlite3
import time
import statistics
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from .storage import SNAPSHOT_DB_PATH, connect

router = APIRouter(tags=["backtest"])


def _ensure_parent_registry(conn: Optional[sqlite3.Connection] = None) -> sqlite3.Connection:
    c = conn or connect()
    cur = c.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parent_registry (
          parent TEXT PRIMARY KEY,
          canonical_narrative TEXT,
          tags TEXT,
          first_seen INTEGER,
          last_seen INTEGER
        )
        """
    )
    c.commit()
    return c


def _migrate_parents_if_empty(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM parent_registry")
    if (cur.fetchone()["n"] or 0) > 0:
        return

    # Seed registry from tracked_pairs (best-effort)
    cur.execute(
        """
        SELECT tp.parent,
               MAX(tp.last_seen) AS last_seen,
               MIN(tp.first_seen) AS first_seen
        FROM tracked_pairs tp
        GROUP BY tp.parent
        """
    )
    parents = cur.fetchall()
    for p in parents:
        parent = p["parent"]
        cur.execute(
            """
            SELECT narrative
            FROM tracked_pairs
            WHERE parent = ?
              AND narrative IS NOT NULL
              AND narrative <> ''
            ORDER BY last_seen DESC
            LIMIT 1
            """,
            (parent,),
        )
        row = cur.fetchone()
        canonical = row["narrative"] if row else None
        cur.execute(
            """
            INSERT OR IGNORE INTO parent_registry(parent, canonical_narrative, tags, first_seen, last_seen)
            VALUES (?, ?, NULL, ?, ?)
            """,
            (parent, canonical, p["first_seen"], p["last_seen"]),
        )
    conn.commit()


@router.get("/backtest/walk")
def backtest_walk(
    narrative: Optional[str] = Query(None, description="Filter by canonical narrative (from parent_registry)"),
    parent: Optional[str] = Query(None, description="Filter by parent symbol"),
    hold: str = Query("h6", description="Hold window: m5|h1|h6|h24"),
    toleranceMin: int = Query(15, ge=1, le=60, description="Time tolerance (minutes) for snapshot alignment"),
    minLiqUsd: float = Query(0.0, ge=0.0, description="Filter by minimum liquidity at exit snapshot"),
    maxEntryAgeHours: Optional[float] = Query(
        None,
        ge=0.0,
        description="Only include trades where (entry time - first_seen) <= this many hours. Omit to disable.",
    ),
) -> Dict[str, Any]:
    """
    Walk-forward backtest using locally stored snapshots:
      - Entry snapshot near (now - hold), within tolerance.
      - Exit snapshot near now, within tolerance.
      - Universe is determined by parent_registry.canonical_narrative (late-bound).
    """
    hold_map = {"m5": 5 * 60, "h1": 3600, "h6": 6 * 3600, "h24": 24 * 3600}
    hold_s = hold_map.get(hold.lower(), 6 * 3600)
    tol_s = toleranceMin * 60
    now = int(time.time())
    t_entry = now - hold_s

    conn = _ensure_parent_registry()
    _migrate_parents_if_empty(conn)
    cur = conn.cursor()

    # Candidate universe:
    args: List[Any] = []
    if parent:
        # Narrow to a single parent
        cur.execute(
            """
            SELECT pair_address, parent, narrative, symbol, first_seen, last_seen
            FROM tracked_pairs
            WHERE UPPER(parent) = ?
            ORDER BY last_seen DESC
            LIMIT 2000
            """,
            (parent.upper(),),
        )
        pairs = cur.fetchall()
    elif narrative:
        # Late-bind via parent_registry.canonical_narrative
        cur.execute(
            """
            SELECT tp.pair_address, tp.parent, tp.narrative, tp.symbol, tp.first_seen, tp.last_seen
            FROM tracked_pairs tp
            JOIN parent_registry pr ON pr.parent = tp.parent
            WHERE pr.canonical_narrative = ?
            ORDER BY tp.last_seen DESC
            LIMIT 2000
            """,
            (narrative,),
        )
        pairs = cur.fetchall()
    else:
        # All tracked
        cur.execute(
            """
            SELECT pair_address, parent, narrative, symbol, first_seen, last_seen
            FROM tracked_pairs
            ORDER BY last_seen DESC
            LIMIT 2000
            """
        )
        pairs = cur.fetchall()

    # Diagnostics
    diag_total_pairs = len(pairs)
    diag_entry_found = 0
    diag_exit_found = 0
    diag_entry_within_tol = 0
    diag_exit_within_tol = 0
    diag_priced_pairs = 0
    diag_liq_ok = 0
    diag_entry_age_kept = 0

    trades: List[Dict[str, Any]] = []
    returns: List[float] = []

    for row in pairs:
        pair = row["pair_address"]

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

        # Entry-age filter (enter-on-new)
        entry_age_hours: Optional[float] = None
        first_seen = row["first_seen"]
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
            "narrative": narrative,  # late-bound filter value (may be None)
            "entryTs": entry["ts"],
            "exitTs": exit_["ts"],
            "entryPrice": p0,
            "exitPrice": p1,
            "exitLiq": exit_["liquidity_usd"],
            "entryAgeHours": entry_age_hours,
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
        "entry_age_kept": diag_entry_age_kept,
    }

    return {"summary": summary, "diagnostics": diagnostics, "trades": trades}

