# backend/app/tools/synthetic_backfill.py
from __future__ import annotations

import argparse
import os
import sqlite3
import time
from typing import Any, Dict, Iterable, List, Optional


# ----------------------------
# Tiny helpers used by tests
# ----------------------------

def _child_pair(item: Dict[str, Any] | None) -> Optional[str]:
    """
    Return a pair identifier from various possible shapes.
    Tests tolerate None when the key is absent.
    """
    if not isinstance(item, dict):
        return None
    return item.get("pairAddress") or item.get("pair_address") or item.get("address")


def _filtered(raw: Dict[str, Any] | None) -> bool:
    """
    Minimal boolean predicate used by tests to verify safe key handling.
    Interprets:
      - buys/sells from txns.h24
      - liquidity.usd
    Returns True/False; never raises on missing keys.
    """
    if not isinstance(raw, dict):
        return False

    txns = raw.get("txns") or {}
    h24 = txns.get("h24") or {}
    buys = int(h24.get("buys") or 0)
    sells = int(h24.get("sells") or 0)

    liq = (raw.get("liquidity") or {}).get("usd")
    try:
        liq_usd = float(liq) if liq is not None else 0.0
    except (TypeError, ValueError):
        liq_usd = 0.0

    return (buys - sells) >= 0 and buys >= 1 and liq_usd >= 0.0


# ----------------------------
# DB utilities for smoke/backfill
# ----------------------------

def _db_path() -> str:
    """
    Resolve sqlite db path:
      - PRIMECIPHER_DB_PATH env var, or
      - ./primecipher.db
    """
    return os.environ.get("PRIMECIPHER_DB_PATH", "primecipher.db")


def _connect() -> sqlite3.Connection:
    """
    Open a connection and ensure row factory for dict-like access.
    Tests may monkeypatch sqlite3 in other modules; keep this local.
    """
    path = _db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """
    Ensure the tables used by backtest_walk AND smoke debug exist.
      - tracked_pairs (first_seen/last_seen in seconds)
      - snapshots (timeseries, ts in seconds)
      - pair_snapshots (legacy mirror for smoke debug printing)
    """
    cur = conn.cursor()
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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
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
    # Legacy/debug table that some scripts still peek at
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


def _upsert_tracked_pair(
    conn: sqlite3.Connection,
    pair_address: str,
    parent: str,
    narrative: Optional[str],
    symbol: Optional[str],
    first_seen: int,
    last_seen: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT first_seen FROM tracked_pairs WHERE pair_address = ?",
        (pair_address,),
    )
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """
            INSERT INTO tracked_pairs (pair_address, parent, narrative, symbol, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (pair_address, parent, narrative, symbol, first_seen, last_seen),
        )
    else:
        cur.execute(
            "UPDATE tracked_pairs SET parent=?, narrative=?, symbol=?, last_seen=? WHERE pair_address=?",
            (parent, narrative, symbol, last_seen, pair_address),
        )
    conn.commit()


def _insert_snapshot(
    conn: sqlite3.Connection,
    pair_address: str,
    ts_sec: int,
    price_usd: float,
    liquidity_usd: float,
    fdv_usd: Optional[float] = None,
    vol24h_usd: Optional[float] = None,
) -> None:
    """
    Insert into both snapshots and pair_snapshots for compatibility.
    """
    cur = conn.cursor()
    args = (pair_address, ts_sec, price_usd, liquidity_usd, fdv_usd, vol24h_usd)
    cur.execute(
        """
        INSERT OR REPLACE INTO snapshots
        (pair_address, ts, price_usd, liquidity_usd, fdv_usd, vol24h_usd)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        args,
    )
    cur.execute(
        """
        INSERT OR REPLACE INTO pair_snapshots
        (pair_address, ts, price_usd, liquidity_usd, fdv_usd, vol24h_usd)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        args,
    )
    conn.commit()


# ----------------------------
# Discovery stub
# ----------------------------

def _discover_pairs(narrative: Optional[str], parent: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
    """
    Light stub discovery that never performs network I/O in tests or CI.
    """
    parent_sym = (parent or "PARENT").upper()
    out: List[Dict[str, Any]] = []
    n = max(0, int(limit))
    for i in range(n):
        out.append(
            {
                "symbol": f"CHILD{i+1}",
                "pairAddress": f"{parent_sym}_PAIR_{i+1}",
                "txns": {"h24": {"buys": 1, "sells": 0}},
                "liquidity": {"usd": 50_000.0 + i},  # give them decent liq for filters
            }
        )
    return out


# ----------------------------
# CLI entry (used by smoke.sh)
# ----------------------------

def _snap_now_epoch() -> int:
    return int(time.time())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synthetic backfill entry snapshots from stub discovery"
    )
    parser.add_argument("--window", choices=["m5", "h1", "h6", "h24"], default="h6")
    parser.add_argument("--narrative", default=None)
    parser.add_argument("--parent", default=None)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    hold_map = {"m5": 300, "h1": 3600, "h6": 6 * 3600, "h24": 24 * 3600}
    hold_s = hold_map.get(str(args.window).lower(), 6 * 3600)

    now = _snap_now_epoch()              # seconds
    entry_ts = now - hold_s              # seconds

    conn = _connect()
    _ensure_schema(conn)

    discovered = _discover_pairs(args.narrative, args.parent, limit=int(args.limit))

    # Write tracked_pairs + entry/exit snapshots in SECONDS to match backtest_walk
    created_entries = 0
    ensured_exits = 0
    parent_sym = (args.parent or "PARENT").upper()

    for child in discovered:
        pair = _child_pair(child) or f"{parent_sym}_PAIR_AUTO_{created_entries+1}"
        symbol = child.get("symbol")
        liq = (child.get("liquidity") or {}).get("usd") or 0.0

        _upsert_tracked_pair(
            conn=conn,
            pair_address=pair,
            parent=parent_sym,
            narrative=args.narrative,
            symbol=symbol,
            first_seen=entry_ts,
            last_seen=now,
        )

        # Entry snapshot (at entry_ts)
        _insert_snapshot(
            conn,
            pair_address=pair,
            ts_sec=entry_ts,
            price_usd=1.00,             # deterministic
            liquidity_usd=float(liq),
            fdv_usd=None,
            vol24h_usd=None,
        )
        created_entries += 1

        # Exit snapshot (at now)
        _insert_snapshot(
            conn,
            pair_address=pair,
            ts_sec=now,
            price_usd=1.05,             # +5% to ensure a non-zero return
            liquidity_usd=float(liq),
            fdv_usd=None,
            vol24h_usd=None,
        )
        ensured_exits += 1

    dbp = os.path.abspath(_db_path())
    print(
        f"[backfill] pairs: {len(discovered)} • window={args.window} • entry_ts={entry_ts} • db={dbp}"
    )
    print(
        f"[backfill] synthetic entries created: {created_entries}, exit ensured: {ensured_exits}, window={args.window}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
