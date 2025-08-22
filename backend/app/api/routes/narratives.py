# backend/app/api/routes/narratives.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from ...storage import connect
from ...seeds import load_narrative_seeds  # fallback only

router = APIRouter(prefix="", tags=["narratives"])


def _ensure_parent_registry() -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parent_registry (
          parent TEXT PRIMARY KEY,
          canonical_narrative TEXT,
          tags TEXT,             -- JSON string (optional)
          first_seen INTEGER,
          last_seen INTEGER
        )
        """
    )
    conn.commit()


def _maybe_migrate_from_tracked_pairs() -> None:
    """
    If parent_registry is empty, populate from tracked_pairs using the most recent non-empty narrative per parent.
    This is a one-time, best-effort bootstrap so the UI isn't blank.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM parent_registry")
    if (cur.fetchone()["n"] or 0) > 0:
        return

    # Pull latest (by last_seen) narrative per parent, if any
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


@router.get("/narratives")
def list_narratives() -> Dict[str, Any]:
    """
    DB-driven narratives:
      1) parent_registry.canonical_narrative (primary)
      2) If empty (first-run), fall back to seeds to avoid an empty UI.
    """
    _ensure_parent_registry()
    _maybe_migrate_from_tracked_pairs()

    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT canonical_narrative AS key,
               COUNT(*) AS num_parents
        FROM parent_registry
        WHERE canonical_narrative IS NOT NULL AND canonical_narrative <> ''
        GROUP BY canonical_narrative
        ORDER BY canonical_narrative
        """
    )
    rows = cur.fetchall()

    items: List[Dict[str, Any]] = []
    for r in rows:
        key = r["key"]
        cur.execute("SELECT parent FROM parent_registry WHERE canonical_narrative = ? ORDER BY parent", (key,))
        parents = [x["parent"] for x in cur.fetchall()]
        items.append({"key": key, "parents": parents, "num_parents": int(r["num_parents"] or 0)})

    if not items:
        # Fallback only to keep the app navigable on a clean DB (CI/first-run).
        seeds = load_narrative_seeds()
        for s in seeds:
            key = s.get("narrative")
            parents = [
                (p.get("symbol") or "").upper()
                for p in (s.get("parents") or [])
                if p.get("symbol")
            ]
            items.append({"key": key, "parents": parents, "num_parents": len(parents)})
        # de-dupe and sort
        dedup: Dict[str, Dict[str, Any]] = {i["key"]: i for i in items if i.get("key")}
        items = sorted(dedup.values(), key=lambda x: x["key"])

    return {"narratives": items}

