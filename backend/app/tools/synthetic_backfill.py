# backend/app/tools/synthetic_backfill.py
from __future__ import annotations

import argparse
import time
from typing import Any, Dict, List, Optional

import httpx
from app.storage import SNAPSHOT_DB_PATH, connect, insert_snapshot

HOLD_MAP = {"m5": 5*60, "h1": 3600, "h6": 6*3600, "h24": 24*3600}

def _rows(q: str, args: tuple = ()) -> List[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(q, args)
    out = []
    for r in cur.fetchall():
        out.append({k: r[k] for k in r.keys()})
    return out

def _have_snapshot_near(pair: str, ts: int, tol_s: int = 60) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM pair_snapshots WHERE pair_address=? AND ABS(ts - ?) <= ? LIMIT 1",
        (pair, ts, tol_s),
    )
    return cur.fetchone() is not None

async def main() -> None:
    p = argparse.ArgumentParser(description="Synthetic backfill entry snapshots from Dexscreener priceChange")
    p.add_argument("--window", default="h6", choices=list(HOLD_MAP.keys()), help="Hold window to backfill")
    p.add_argument("--narrative", default=None, help="Filter tracked pairs by narrative")
    p.add_argument("--parent", default=None, help="Filter tracked pairs by parent symbol")
    p.add_argument("--max", type=int, default=500, help="Max pairs to backfill")
    args = p.parse_args()

    hold = args.window
    hold_s = HOLD_MAP[hold]
    now = int(time.time())
    entry_ts = now - hold_s

    # Choose tracked pairs
    q = "SELECT pair_address, parent, narrative FROM tracked_pairs WHERE 1=1"
    a: List[Any] = []
    if args.narrative:
        q += " AND narrative = ?"
        a.append(args.narrative)
    if args.parent:
        q += " AND parent = ?"
        a.append(args.parent.upper())
    q += " ORDER BY last_seen DESC LIMIT ?"
    a.append(args.max)
    pairs = _rows(q, tuple(a))

    if not pairs:
        print("No tracked pairs found.")
        return

    print(f"[backfill] pairs: {len(pairs)} • window={hold} • entry_ts={entry_ts}")

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "narrative-heatmap/backfill"}) as client:
        created = 0
        ensured_exit = 0

        for row in pairs:
            pair = row["pair_address"]
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair}"
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                p0 = (data.get("pairs") or [None])[0] or {}
                price_now = p0.get("priceUsd")
                price_change = (p0.get("priceChange") or {}).get(hold)
                liq_usd = ((p0.get("liquidity") or {}).get("usd"))
                fdv_usd = p0.get("fdv")
                vol24h = (p0.get("volume") or {}).get("h24")
                if price_now is None or price_change is None:
                    continue

                # Deduce entry price from % change (e.g., +5% => 0.05)
                # price_change is percent; convert to decimal and invert
                dec = float(price_change) / 100.0
                if (1.0 + dec) == 0:
                    continue
                price_entry = float(price_now) / (1.0 + dec)

                # Insert synthetic entry snapshot (skip if one exists near that ts)
                if not _have_snapshot_near(pair, entry_ts, tol_s=60):
                    insert_snapshot(
                        pair, entry_ts,
                        price_entry,
                        float(liq_usd) if liq_usd is not None else None,
                        float(fdv_usd) if fdv_usd is not None else None,
                        float(vol24h) if vol24h is not None else None,
                    )
                    created += 1

                # Ensure we also have an "exit" snapshot near now (optional)
                if not _have_snapshot_near(pair, now, tol_s=60):
                    insert_snapshot(
                        pair, now,
                        float(price_now),
                        float(liq_usd) if liq_usd is not None else None,
                        float(fdv_usd) if fdv_usd is not None else None,
                        float(vol24h) if vol24h is not None else None,
                    )
                    ensured_exit += 1

            except Exception:
                # best-effort; skip pair on error
                continue

    print(f"[backfill] synthetic entries created: {created}, exit ensured: {ensured_exit}, window={hold}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

