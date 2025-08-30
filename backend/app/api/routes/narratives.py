"""API routes for narratives."""

from fastapi import APIRouter

from ...schemas import NarrativesResp
from ...seeds import list_narrative_names
from ...storage import last_refresh_ts

router = APIRouter()


@router.get("/narratives", response_model=NarrativesResp)
def list_narratives() -> dict:
    """Get list of available narratives.

    :return: List of available narratives.
    """
    return {"items": list_narrative_names(), "lastRefresh": last_refresh_ts()}
