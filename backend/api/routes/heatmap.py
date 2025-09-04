"""API routes for heatmap."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/heatmap")
def get_heatmap() -> dict:
    """Get heatmap data.

    :return: Heatmap data with items, stale status, and last updated timestamp.
    """
    return {"items": [], "stale": True, "lastUpdated": None}
