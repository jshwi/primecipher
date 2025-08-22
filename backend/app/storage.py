# backend/app/storage.py
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Iterable, Optional

SNAPSHOT_DB_PATH = os.getenv("SNAPSHOT_DB_PATH", "./data/snapshots.db")
Path(SNAPSHOT_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(SNAPSHOT_DB_PATH, timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tracked_pairs (
        pair_address TEXT PRIMARY KEY,
        parent TEXT NOT NULL,
        narrative TEXT NOT NULL,
        symbol TEXT,
        first_seen INTEGER NOT NULL,
        last_seen INTEGER NOT NULL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tracked_pairs_last_seen ON tracked_pairs(last_seen)")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pair_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair_address TEXT NOT NULL,
        ts INTEGER NOT NULL,
        price_usd REAL,
        liquidity_usd REAL,
        fdv_usd REAL,
        vol24h_usd REAL,
        FOREIGN KEY(pair_address) REFERENCES tracked_pairs(pair_address)
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_pair_ts ON pair_snapshots(pair_address, ts)")
    conn.commit()


def upsert_tracked_pair(pair_address: str, parent: str, narrative: str, symbol: Optional[str]) -> None:
    now = int(time.time())
    conn = connect()
    cur = conn.cursor()
    # REPLACE keeps it simple for MVP; we preserve first_seen if exists
    cur.execute("SELECT first_seen FROM tracked_pairs WHERE pair_address = ?", (pair_address,))
    row = cur.fetchone()
    first_seen = row["first_seen"] if row else now
    cur.execute("""
        INSERT INTO tracked_pairs(pair_address, parent, narrative, symbol, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(pair_address) DO UPDATE SET
          parent=excluded.parent,
          narrative=excluded.narrative,
          symbol=excluded.symbol,
          last_seen=excluded.last_seen
    """, (pair_address, parent, narrative, symbol, first_seen, now))
    conn.commit()


def recent_pairs(max_idle_hours: float = 72.0, parents: Optional[Iterable[str]] = None, narrative: Optional[str] = None) -> list[str]:
    conn = connect()
    cur = conn.cursor()
    cutoff = int(time.time() - max_idle_hours * 3600)
    q = "SELECT pair_address FROM tracked_pairs WHERE last_seen >= ?"
    args: list = [cutoff]
    if parents:
        placeholders = ",".join("?" for _ in parents)
        q += f" AND parent IN ({placeholders})"
        args.extend(list(parents))
    if narrative:
        q += " AND narrative = ?"
        args.append(narrative)
    q += " ORDER BY last_seen DESC"
    cur.execute(q, args)
    return [r["pair_address"] for r in cur.fetchall()]


def insert_snapshot(pair_address: str, ts: int, price_usd: Optional[float], liquidity_usd: Optional[float], fdv_usd: Optional[float], vol24h_usd: Optional[float]) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pair_snapshots (pair_address, ts, price_usd, liquidity_usd, fdv_usd, vol24h_usd)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pair_address, ts, price_usd, liquidity_usd, fdv_usd, vol24h_usd))
    conn.commit()

