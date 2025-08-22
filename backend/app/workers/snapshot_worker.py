# backend/app/workers/snapshot_worker.py
from __future__ import annotations

import argparse
import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from app.adapters.onchain import make_onchain_adapter
from app.config import PROVIDER
from app.seeds import load_narrative_seeds
from app.storage import init_db, upsert_tracked_pair, recent_pairs, insert_snapshot


DEX_LATEST_URL = "https://api.dexscreener.com/latest/dex/pairs/solana/{}"

# Tunables (env)
DISCOVERY_LIQ_MIN_USD = float(os.getenv("DISCOVERY_LIQ_MIN_USD", "50000"))
DISCOVERY_VOL24H_MIN_USD = float(os.getenv("DISCOVERY_VOL24H_MIN_USD", "0"))
DISCOVERY_MAX_AGE_HOURS = float(os.getenv("DISCOVERY_MAX_AGE_HOURS", ""))
MAX_IDLE_HOURS = float(os.getenv("SNAPSHOT_MAX_IDLE_HOURS", "72"))  # which tracked pairs to snapshot
CONCURRENCY = int(os.getenv("SNAPSHOT_CONCURRENCY", "16"))


def _child_pair(child: Dict[str, Any]) -> Optional[str]:
    m = child.get("matched") or {}
    addr = m.get("pairAddress")
    if isinstance(addr, str) and addr.strip():
        return addr.strip()
    return None


def _filtered(child: Dict[str, Any]) -> bool:
    if (child.get("liquidityUsd") or 0.0) < DISCOVERY_LIQ_MIN_USD:
        return False
    if (child.get("volume24hUsd") or 0.0) < DISCOVERY_VOL24H_MIN_USD:
        return False
    age = child.get("ageHours")
    if os.getenv("DISCOVERY_MAX_AGE_HOURS"):
        try:
            max_age = float(os.getenv("DISCOVERY_MAX_AGE_HOURS"))
            if age is not None and age > max_age:
                return False
        except Exception:
            pass
    return True


def refresh_tracked_from_seeds() -> int:
    adapter = make_onchain_adapter(PROVIDER)
    seeds = load_narrative_seeds()
    added = 0
    for seed in seeds:
        narrative = seed.get("narrative")
        for p in (seed.get("parents") or []):
            parent = (p.get("symbol") or "").upper()
            if not parent:
                continue
            terms = (p.get("match") or [parent.lower()])
            allow_name = p.get("nameMatchAllowed", True)
            discovery = p.get("discovery") or {}

            # fetch children for this parent
            kids = adapter.fetch_children_for_parent(
                parent_symbol=parent,
                match_terms=terms,
                allow_name_match=allow_name,
                limit=300,
                discovery=discovery,
            )
            for c in kids:
                if not _filtered(c):
                    continue
                pair = _child_pair(c)
                if not pair:
                    continue
                sym = c.get("symbol") or None
                upsert_tracked_pair(pair, parent=parent, narrative=narrative, symbol=sym)
                added += 1
    return added


async def snapshot_once(parents: Optional[List[str]] = None, narrative: Optional[str] = None) -> int:
    targets = recent_pairs(max_idle_hours=MAX_IDLE_HOURS, parents=parents, narrative=narrative)
    if not targets:
        return 0
    ts = int(time.time())

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "narrative-heatmap/0.8"}) as client:
        sem = asyncio.Semaphore(CONCURRENCY)
        async def task(pair_address: str) -> None:
            async with sem:
                try:
                    r = await client.get(DEX_LATEST_URL.format(pair_address))
                    r.raise_for_status()
                    data = r.json()
                    pair = (data.get("pairs") or [None])[0] or {}
                    price = float(pair.get("priceUsd")) if pair.get("priceUsd") is not None else None
                    liq = float((pair.get("liquidity") or {}).get("usd")) if (pair.get("liquidity") or {}).get("usd") is not None else None
                    fdv = float(pair.get("fdv")) if pair.get("fdv") is not None else None
                    vol = float((pair.get("volume") or {}).get("h24")) if (pair.get("volume") or {}).get("h24") is not None else None
                    insert_snapshot(pair_address, ts, price, liq, fdv, vol)
                except Exception:
                    # swallow; best effort
                    pass

        await asyncio.gather(*(task(p) for p in targets))
    return len(targets)


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot worker: refresh tracklist, then snapshot pairs.")
    parser.add_argument("--interval-sec", type=int, default=300, help="Loop interval in seconds (default: 300)")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    init_db()
    while True:
        added = refresh_tracked_from_seeds()
        print(f"[snap] refreshed tracked (candidates added/updated) = {added}")
        count = asyncio.run(snapshot_once())
        print(f"[snap] snapshotted pairs = {count}")
        if args.once:
            break
        time.sleep(max(5, args.interval_sec))


if __name__ == "__main__":
    main()

