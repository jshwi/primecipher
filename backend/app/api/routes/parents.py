# backend/app/api/routes/parents.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional, TypedDict

from fastapi import APIRouter, Body, HTTPException

from ...storage import connect

router = APIRouter(prefix="", tags=["parents"])


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
          last_seen INTEGER
        )
        """
    )
    conn.commit()


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
    tags_str: Optional[str] = None
    if tags is not None:
        try:
            tags_str = json.dumps(tags, ensure_ascii=False)
        except Exception:
            tags_str = str(tags)

    conn = connect()
    cur = conn.cursor()
    # timestamps from tracked_pairs if available
    cur.execute(
        "SELECT MIN(first_seen) AS first_seen, MAX(last_seen) AS last_seen FROM tracked_pairs WHERE parent = ?",
        (parent_sym,),
    )
    row = cur.fetchone() or {"first_seen": None, "last_seen": None}
    cur.execute(
        """
        INSERT INTO parent_registry(parent, canonical_narrative, tags, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(parent) DO UPDATE SET
          canonical_narrative=excluded.canonical_narrative,
          tags=excluded.tags,
          last_seen=COALESCE(excluded.last_seen, parent_registry.last_seen)
        """,
        (parent_sym, canonical, tags_str, row["first_seen"], row["last_seen"]),
    )
    conn.commit()

    return {"parent": parent_sym, "canonicalNarrative": canonical, "tags": tags}

