# backend/app/api/routes/parents.py
# -----------------------------------------------------------------------------
# Parents endpoints
#
# - GET  /parents/{narrative}
#       List parent rows for the narrative using *parent_registry* (late-bound).
#       This replaces the old behavior that filtered by tracked_pairs.narrative.
#
# - POST /parents/{parent}/classify
#       Set/overwrite the canonical narrative (and optional tags) for a parent.
#
# Notes:
# - We keep computation light and local: counts/new24h/survival and children
#   liquidity are derived from tracked_pairs + pair_snapshots. Parent liquidity
#   is left as 0.0 if we don't have a canonical source for it.
# - This module ensures parent_registry exists and can be used without touching
#   storage.py. It does NOT mutate tracked_pairs' legacy narrative.
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, TypedDict

from fastapi import APIRouter, Body, HTTPException, Query

from ...storage import connect

router = APIRouter(prefix="", tags=["parents"])


# --- Shared: ensure registry --------------------------------------------------

def _ensure_parent_registry() -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parent_registry (
          parent TEXT PRIMARY KEY,
          canonical_narrative TEXT,
          tags TEXT,
          first_seen INTEGER,
          last_seen INTEGER,
          -- optional fields for future auto-classifier; harmless if unused
          auto_confidence REAL,
          auto_evidence TEXT,
          source TEXT
        )
        """
    )
    conn.commit()


# --- GET: list parents for a narrative (registry-driven) ---------------------

@router.get("/parents/{narrative}")
def list_parents_for_narrative(
    narrative: str,
    window: str = Query("24h", description="UI hint; used to label the page. Does not change the query."),
) -> Dict[str, Any]:
    """
    List parents for a narrative using *parent_registry.canonical_narrative*.

    Response shape mirrors what the UI expects in ParentsTable.tsx:
    rows: [{
      parent, narrative, childrenCount, childrenNew24h,
      survivalRates: {h24, d7},
      liquidityFunnel: {parentLiquidityUsd, childrenLiquidityUsd},
      topChild: null,  // top child details are fetched by /debug/children separately
      lastUpdated: ISO8601 or null
    }]
    """
    _ensure_parent_registry()
    now = int(time.time())
    day_ago = now - 24 * 3600
    week_ago = now - 7 * 24 * 3600

    conn = connect()
    cur = conn.cursor()

    # Universe = parents whose canonical narrative matches
    cur.execute(
        """
        SELECT parent
        FROM parent_registry
        WHERE canonical_narrative = ?
        ORDER BY parent ASC
        """,
        (narrative,),
    )
    parent_rows = [r["parent"] for r in cur.fetchall()]

    rows: List[Dict[str, Any]] = []

    for parent in parent_rows:
        # Children totals from tracked_pairs
        cur.execute("SELECT COUNT(*) AS n FROM tracked_pairs WHERE parent = ?", (parent,))
        total_children = int(cur.fetchone()["n"] or 0)

        # New children in 24h based on first_seen
        cur.execute(
            "SELECT COUNT(*) AS n FROM tracked_pairs WHERE parent = ? AND first_seen >= ?",
            (parent, day_ago),
        )
        new24 = int(cur.fetchone()["n"] or 0)

        # "Survival h24": share of children with last_seen in last 24h
        cur.execute(
            "SELECT COUNT(*) AS n FROM tracked_pairs WHERE parent = ? AND last_seen >= ?",
            (parent, day_ago),
        )
        alive24 = int(cur.fetchone()["n"] or 0)
        survival_h24 = (alive24 / total_children * 100.0) if total_children else 0.0

        # "Survival d7": share with last_seen in last 7d
        cur.execute(
            "SELECT COUNT(*) AS n FROM tracked_pairs WHERE parent = ? AND last_seen >= ?",
            (parent, week_ago),
        )
        alive7 = int(cur.fetchone()["n"] or 0)
        survival_d7 = (alive7 / total_children * 100.0) if total_children else 0.0

        # Children liquidity: sum latest snapshot liquidity per pair (nearest to now)
        cur.execute(
            """
            SELECT ps.pair_address, ps.liquidity_usd
            FROM pair_snapshots ps
            JOIN (
              SELECT pair_address, MAX(ts) AS ts
              FROM pair_snapshots
              GROUP BY pair_address
            ) last ON last.pair_address = ps.pair_address AND last.ts = ps.ts
            WHERE ps.pair_address IN (
              SELECT pair_address FROM tracked_pairs WHERE parent = ?
            )
            """,
            (parent,),
        )
        children_liq = 0.0
        for r in cur.fetchall():
            try:
                children_liq += float(r["liquidity_usd"] or 0.0)
            except Exception:
                pass

        # We don't have a canonical "parent liquidity" source here; leave 0.0.
        parent_liq = 0.0

        # lastUpdated: use latest last_seen for any child
        cur.execute(
            "SELECT MAX(last_seen) AS last_seen FROM tracked_pairs WHERE parent = ?",
            (parent,),
        )
        lu = cur.fetchone()["last_seen"]
        last_updated = None
        if isinstance(lu, int) and lu > 0:
            # ISO-ish without tz to keep it lightweight (UI can display raw)
            last_updated = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(lu))

        rows.append(
            {
                "parent": parent,
                "narrative": narrative,
                "childrenCount": total_children,
                "childrenNew24h": new24,
                "survivalRates": {"h24": survival_h24, "d7": survival_d7},
                "liquidityFunnel": {
                    "parentLiquidityUsd": parent_liq,
                    "childrenLiquidityUsd": children_liq,
                },
                "topChild": None,  # fetched lazily via /debug/children in the UI
                "lastUpdated": last_updated,
            }
        )

    return {"window": window, "rows": rows}


# --- POST: classify parent (kept from earlier change) ------------------------

class ClassifyBody(TypedDict, total=False):
    canonicalNarrative: str
    tags: Any  # list/dict/str


@router.post("/parents/{parent}/classify")
def classify_parent(parent: str, body: ClassifyBody = Body(...)) -> Dict[str, Any]:
    """
    Set/overwrite the canonical narrative (and optional tags) for a parent.
    This is the admin 'classification' step that decouples discovery from narrative membership.
    """
    _ensure_parent_registry()
    parent_sym = (parent or "").upper().strip()
    if not parent_sym:
        raise HTTPException(status_code=400, detail="Missing parent")

    canonical = (body.get("canonicalNarrative") or "").strip()
    if not canonical:
        raise HTTPException(status_code=400, detail="Missing canonicalNarrative")

    tags = body.get("tags", None)
    try:
        tags_str: Optional[str] = json.dumps(tags, ensure_ascii=False) if tags is not None else None
    except Exception:
        tags_str = str(tags) if tags is not None else None

    conn = connect()
    cur = conn.cursor()
    # derive timestamps from tracked_pairs if available
    cur.execute(
        "SELECT MIN(first_seen) AS first_seen, MAX(last_seen) AS last_seen FROM tracked_pairs WHERE parent = ?",
        (parent_sym,),
    )
    row = cur.fetchone() or {"first_seen": None, "last_seen": None}
    cur.execute(
        """
        INSERT INTO parent_registry(parent, canonical_narrative, tags, first_seen, last_seen, source)
        VALUES (?, ?, ?, ?, ?, 'override')
        ON CONFLICT(parent) DO UPDATE SET
          canonical_narrative=excluded.canonical_narrative,
          tags=excluded.tags,
          last_seen=COALESCE(excluded.last_seen, parent_registry.last_seen),
          source='override'
        """,
        (parent_sym, canonical, tags_str, row["first_seen"], row["last_seen"]),
    )
    conn.commit()

    return {"parent": parent_sym, "canonicalNarrative": canonical, "tags": tags}

