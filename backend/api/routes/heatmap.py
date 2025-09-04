"""API routes for heatmap."""

import os
import time

from fastapi import APIRouter

from ...parents import TOP_N, _with_scores
from ...repo import list_parents
from ...seeds import list_narrative_names
from ...storage import get_meta, get_parents

# Read TTL from environment variable
TTL = int(os.getenv("REFRESH_TTL_SEC", "900"))

router = APIRouter()


@router.get("/heatmap")
def get_heatmap() -> dict:
    """Get heatmap data.

    :return: Heatmap data with items, stale status, and last updated timestamp.
    """
    items = []
    computed_at_values = []

    for name in list_narrative_names():
        # Get parent data from database or storage
        parent_items = list_parents(name) or get_parents(name) or []

        # Apply scoring and limit to TOP_N
        scored = _with_scores(parent_items)[:TOP_N]
        count = len(scored)

        # Calculate average score
        agg = (
            sum(it.get("score", 0.0) for it in scored) / count
            if count
            else 0.0
        )

        # Get metadata for this narrative
        meta = get_meta(name) or {}
        computed_at = meta.get("computedAt")
        is_stale = (computed_at is None) or (time.time() - computed_at > TTL)

        # Collect computed_at values for top-level calculation
        if computed_at is not None:
            computed_at_values.append(computed_at)

        # Append narrative data with lastUpdated and stale fields
        items.append(
            {
                "name": name,
                "score": round(agg, 4),
                "count": count,
                "lastUpdated": computed_at,
                "stale": is_stale,
            },
        )

    # Sort by score descending
    items.sort(
        key=lambda x: (
            float(x["score"]) if isinstance(x["score"], (int, float)) else 0.0
        ),
        reverse=True,
    )

    # Calculate top-level fields
    last_updated = max(computed_at_values) if computed_at_values else None
    any_stale = any(item["stale"] for item in items)

    return {"items": items, "stale": any_stale, "lastUpdated": last_updated}
