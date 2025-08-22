# backend/app/tools/synthetic_backfill.py
from __future__ import annotations

import argparse
import time
from typing import Any, Dict, List, Optional

import httpx

from app.storage import connect, insert_snapshot
from app.seeds import load_narrative_seeds
from app.adapters.onchain import make_onchain_adapter
from app.config import PROVIDER

HOLD_MAP = {"m5": 5 * 60, "h1": 3600, "h6": 6 * 3600, "h24": 24 * 3600}
DEX_LATEST_URL = "https://api.dexscreener.com/latest/dex/pairs/solana/{}"

# Discovery filters (match snapshot_worker defaults; lightweight and safe)
DISCOVERY_LIQ_MIN_USD = 50_000.0
DISCOVERY_VOL24H_MIN_USD = 0.0
DISCOVERY_MAX_AGE_HOURS: Optional[float] = None  # no age cap here, keep broad


def _rows(q: str, args: tuple = ()) -> List[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(q, args)
    return [{k: r[k] for k in r.keys()} for r in cur.fetchall()]


def _upsert_tracked(pair_address: str, parent: str, narrative: str, symbol: Optional[str]) -> None:
    # small inline upsert to avoid importing many helpers
    conn = connect()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute("SELECT first_seen FROM tracked_pairs WHERE pair_address = ?", (pair_address,))
    row = cur.fetchone()
    first_seen = row["first_seen"] if row else now
    cur.execute(
        """
        INSERT INTO tracked_pairs(pair_address, parent, narrative, symbol, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(pair_address) DO UPDATE SET
          parent=excluded.parent,
          narrative=excluded.narrative,
          symbol=excluded.symbol,
          last_seen=excluded.last_seen
        """,
        (pair_address, parent, narrative, symbol, first_seen, now),
    )
    conn.commit()


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
    if DISCOVERY_MAX_AGE_HOURS is not None:
        age = child.get("ageHours")
        if age is not None and age > DISCOVERY_MAX_AGE_HOURS:
            return False
    return True


def _seed_tracked_from_seeds(narrative: Optional[str], parent: Optional[str]) -> int:
    """Populate tracked_pairs from seeds (same discovery as worker) when empty."""
    seeds = load_narrative_seeds()
    adapter = make_onchain_adapter(PROVIDER)
    added = 0

    def parents_for(narr: Dict[str, Any]) -> List[Dict[str, Any]]:
        ps = narr.get("parents") or []
        if parent:
            return [p for p in ps if (p.get("symbol") or "").upper() == parent.upper()]
        return ps

    for s in seeds:
        narr_key = s.get("narrative")
        if narrative and narr_key != narrative:
            continue
        for p in parents_for(s):
            sym = (p.get("symbol") or "").upper()
            if not sym:
                continue
            terms: List[str] = (p.get("match") or [sym.lower()])
            allow_name = p.get("nameMatchAllowed", True)
            discovery = p.get("discovery") or {}
            kids = adapter.fetch_children_for_parent(
                parent_symbol=sym,
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
                _upsert_tracked(pair, parent=sym, narrative=narr_key, symbol=c.get("symbol") or None)
                added += 1
    return added


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

    # 1) Load tracked pairs; if none match, seed from seeds, then reload
    def load_pairs() -> List[Dict[str, Any]]:
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
        return _rows(q, tuple(a))

    pairs = load_pairs()
    if not pairs:
        seeded = _seed_tracked_from_seeds(args.narrative, args.parent)
        pairs = load_pairs()

    if not pairs:
        print("No tracked pairs found.")
        return

    print(f"[backfill] pairs: {len(pairs)} • window={hold} • entry_ts={entry_ts}")

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "narrative-heatmap/backfill"}) as client:
        created = 0
        ensured_exit = 0

        for row in pairs:
            pair = row["pair_address"]
            url = DEX_LATEST_URL.format(pair)
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

                dec = float(price_change) / 100.0
                if (1.0 + dec) == 0:
                    continue
                price_entry = float(price_now) / (1.0 + dec)

                if not _have_snapshot_near(pair, entry_ts, tol_s=60):
                    insert_snapshot(
                        pair, entry_ts,
                        price_entry,
                        float(liq_usd) if liq_usd is not None else None,
                        float(fdv_usd) if fdv_usd is not None else None,
                        float(vol24h) if vol24h is not None else None,
                    )
                    created += 1

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
                # best-effort; skip this pair
                continue

    print(f"[backfill] synthetic entries created: {created}, exit ensured: {ensured_exit}, window={hold}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

