# replace file contents with this minimal variant if needed
from fastapi import APIRouter
from ...seeds import list_narrative_names
from ...storage import last_refresh_ts

router = APIRouter()

@router.get("/narratives")
def list_narratives() -> dict:
    # items is an array of narrative names
    return {"items": list_narrative_names(), "lastRefresh": last_refresh_ts()}
