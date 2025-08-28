
from fastapi import APIRouter, Query
from typing import Any, Dict
from ...seeds import list_narrative_names
from ...storage import last_refresh_ts

router = APIRouter()

@router.get("/narratives")
def list_narratives(window: str = Query(default="24h")) -> Dict[str, Any]:
    items = [{"narrative": n, "count": None} for n in list_narrative_names()]
    return {"window": window, "lastRefreshTs": last_refresh_ts(), "items": items}
