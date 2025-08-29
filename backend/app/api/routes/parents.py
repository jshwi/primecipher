from fastapi import APIRouter, Path, Query, HTTPException
from typing import Any, Dict
from ...seeds import list_narrative_names
from ...storage import get_parents
from ...repo import list_parents as list_parents_db
from ...schemas import ParentsResp

router = APIRouter()

@router.get("/parents/{narrative}", response_model=ParentsResp)
def get_parents_for_narrative(
    narrative: str = Path(..., min_length=1),
    window: str = Query(default="24h")
) -> Dict[str, Any]:
    if narrative not in set(list_narrative_names()):
        raise HTTPException(status_code=404, detail="unknown narrative")
    items = list_parents_db(narrative) or get_parents(narrative)
    return {"narrative": narrative, "window": window, "items": items}
