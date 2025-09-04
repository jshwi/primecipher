"""API routes for heatmap."""

from fastapi import APIRouter

from ...parents import TOP_N, _with_scores
from ...repo import list_parents
from ...seeds import list_narrative_names
from ...storage import get_parents

router = APIRouter()


@router.get("/heatmap")
def get_heatmap() -> dict:
    """Get heatmap data.

    :return: Heatmap data with items, stale status, and last updated timestamp.
    """
    items = []

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

        # Append narrative data
        items.append({"name": name, "score": round(agg, 4), "count": count})

    # Sort by score descending
    items.sort(key=lambda x: x["score"], reverse=True)

    return {"items": items, "stale": False, "lastUpdated": None}
