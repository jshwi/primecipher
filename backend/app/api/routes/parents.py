from fastapi import APIRouter, Path, Query, HTTPException
from typing import Any, Dict
from ...seeds import list_narrative_names
from ...storage import get_parents

router = APIRouter()

@router.get("/parents/{narrative}")
def get_parents_for_narrative(
    narrative: str = Path(..., min_length=1),
    window: str = Query(default="24h")
) -> Dict[str, Any]:
    if narrative not in set(list_narrative_names()):
        raise HTTPException(status_code=404, detail="unknown narrative")
    return {"narrative": narrative, "window": window, "items": get_parents(narrative)}
