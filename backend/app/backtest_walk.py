# backend/app/backtest_walk.py
from __future__ import annotations

import os
import time
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

# Router tag kept stable for wiring in main.py
router = APIRouter(tags=["backtest-walk"])


def _db_path() -> str:
    """
    Resolve the sqlite database path.

    Priority:
      - Env override: PRIMECIPHER_DB_PATH
      - Fallback: ./primecipher.db (relative to current working directory)

    This mirrors smoke.sh and keeps local/dev/CI consistent without special cases.
    """
    return os.environ.get("PRIMECIPHER_DB_PATH", "primecipher.db")


def _connect() -> sqlite3.Connection:
    """
    Patch-friendly connector that uses *this module's* sqlite3 symbol.

    Tests monkeypatch `mod.sqlite3` and assert the returned type, so keep the
    `sqlite3.connect` reference local to this module.
    """
    path = _db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """
    Create required tables on THIS connection (avoids divergent files/handles).
    Safe to call repeatedly.

    We align with what synthetic_backfill.py and storage paths expect:
      - tracked_pairs
      - pair_snapshots  (NOT 'snapshots')
    """
    cur = conn.cursor()

    # tracked_pairs: holds first/last seen metadata
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tracked_pairs (
            pair_address TEXT PRIMARY KEY,
            parent       TEXT,
            narrative    TEXT,
            symbol       TEXT,
            first_seen   INTEGER,
            last_seen    INTEGER
        )
        """
    )

    # pair_snapshots: timeseries pricing/liquidity (schema used by backfill + smoke)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pair_snapshots (
            pair_address   TEXT,
            ts             INTEGER,
            price_usd      REAL,
            liquidity_usd  REAL,
            fdv_usd        REAL,
            vol24h_usd     REAL,
            PRIMARY KEY (pair_address, ts)
        )
        """
    )

    conn.commit()


@router.get("/backtest/walk")
def backtest_walk(
    narrative: Optional[str] = Query(
        None, description="Filter tracked pairs by narrative"
    ),
    parent: Optional[str] = Query(
        None, description="Filter tracked pairs by parent symbol"
    ),
    hold: str = Query("h6", description="Hold window: m5|h1|h6|h24"),
    toleranceMin: int = Query(
        15, ge=1, le=60, description="Time tolerance (minutes) for snapshot alignment"
    ),
    minLiqUsd: float = Query(
        0.0, ge=0.0, description="Filter by minimum liquidity at exit snapshot"
    ),
    maxEntryAgeHours: Optional[float] = Query(
        None,
        ge=0.0,
        description=(
            "Only include trades where (entry ts - first_seen) <= this many hours. "
            "Omit to disable."
        ),
    ),
) -> Dict[str, Any]:
    """
    Walk-forward backtest using locally stored snapshots:
      - Entry snapshot near (now - hold), within tolerance.
      - Exit snapshot near now, within tolerance.
      - Optional 'enter-on-new' via maxEntryAgeHours.
      - Return = (price_exit / price_entry - 1).

    Returns a stable shape for API/CI consumers:
      {
        "params": {...},
        "summary": {"count": int, "note": Optional[str]},
        "results": [
           {
             "pair": str, "parent": str, "narrative": str,
             "entry": {"ts": int, "price_usd": float, "liq": float},
             "exit":  {"ts": int, "price_usd": float, "liq": float},
             "return": float
           }, ...
        ]
      }
    """
    hold_map = {"m5": 300, "h1": 3600, "h6": 6 * 3600, "h24": 24 * 3600}
    hold_s = hold_map.get(hold.lower(), 6 * 3600)
    tol_s = toleranceMin * 60
    now = int(time.time())
    t_entry = now - hold_s

    # Open connection and ensure schema on THIS handle.
    conn = _connect()
    _ensure_schema(conn)
    cur = conn.cursor()

    # Select candidate pairs (include first_seen for entry-age filter)
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

    results: List[Dict[str, Any]] = []

    for row in pairs:
        addr = row["pair_address"]
        par = row["parent"]
        narr = row["narrative"]
        first_seen = int(row["first_seen"] or 0)

        # Entry snapshot nearest to t_entry within tolerance (PAIR_SNAPSHOTS)
        cur.execute(
            "SELECT ts, price_usd, liquidity_usd FROM pair_snapshots "
            "WHERE pair_address=? AND ABS(ts-?) <= ? "
            "ORDER BY ABS(ts-?) ASC LIMIT 1",
            (addr, t_entry, tol_s, t_entry),
        )
        e = cur.fetchone()
        if not e:
            continue
        ts_entry, price_entry, liq_entry = e

        # Optional 'enter-on-new' constraint: age at entry vs first_seen
        if maxEntryAgeHours is not None and (int(ts_entry) - first_seen) > maxEntryAgeHours * 3600:
            continue

        # Exit snapshot nearest to now within tolerance (PAIR_SNAPSHOTS)
        cur.execute(
            "SELECT ts, price_usd, liquidity_usd FROM pair_snapshots "
            "WHERE pair_address=? AND ABS(ts-?) <= ? "
            "ORDER BY ABS(ts-?) ASC LIMIT 1",
            (addr, now, tol_s, now),
        )
        x = cur.fetchone()
        if not x:
            continue
        ts_exit, price_exit, liq_exit = x

        # Basic guards + liquidity screen
        if price_entry is None or price_exit is None or float(price_entry) <= 0.0:
            continue
        if (liq_exit or 0.0) < minLiqUsd:
            continue

        ret = float(price_exit) / float(price_entry) - 1.0
        results.append(
            {
                "pair": addr,
                "parent": par,
                "narrative": narr,
                "entry": {
                    "ts": int(ts_entry),
                    "price_usd": float(price_entry),
                    "liq": float(liq_entry or 0.0),
                },
                "exit": {
                    "ts": int(ts_exit),
                    "price_usd": float(price_exit),
                    "liq": float(liq_exit or 0.0),
                },
                "return": float(ret),
            }
        )

    summary_note = ""
    if not results:
        summary_note = (
            "no trades matched criteria; ensure snapshots exist within tolerance "
            "and consider relaxing filters"
        )

    return {
        "params": {
            "narrative": narrative,
            "parent": parent.upper() if parent else None,
            "hold": hold,
            "toleranceMin": toleranceMin,
            "minLiqUsd": minLiqUsd,
            "maxEntryAgeHours": maxEntryAgeHours,
        },
        "summary": {
            "count": len(results),
            "note": summary_note or None,
        },
        "results": results,
    }
