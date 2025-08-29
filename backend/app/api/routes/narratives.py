from fastapi import APIRouter
from ...seeds import list_narrative_names
from ...storage import last_refresh_ts
from ...schemas import NarrativesResp

router = APIRouter()

@router.get("/narratives", response_model=NarrativesResp)
def list_narratives() -> dict:
    return {"items": list_narrative_names(), "lastRefresh": last_refresh_ts()}
