from fastapi import APIRouter, Path, Query, HTTPException
from typing import Any, Dict
import base64, json

from ...seeds import list_narrative_names
from ...storage import get_parents
from ...repo import list_parents as list_parents_db
from ...schemas import ParentsResp
from ...parents import _with_scores, TOP_N

router = APIRouter()

def _enc_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"o": offset}).encode()).decode()

def _dec_cursor(cursor: str) -> int:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        off = int(data.get("o", 0))
        if off < 0:
            raise ValueError
        return off
    except Exception:
        raise HTTPException(status_code=400, detail="invalid cursor")

@router.get("/parents/{narrative}", response_model=ParentsResp)
def get_parents_for_narrative(
    narrative: str = Path(..., min_length=1),
    window: str = Query(default="24h"),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> Dict[str, Any]:
    if narrative not in set(list_narrative_names()):
        raise HTTPException(status_code=404, detail="unknown narrative")

    # Load & score (keep consistent with compute_all cap)
    items = list_parents_db(narrative) or get_parents(narrative)
    items = _with_scores(items)[:TOP_N]

    start = _dec_cursor(cursor) if cursor else 0
    end = min(start + limit, len(items))
    page = items[start:end]
    next_cursor = _enc_cursor(end) if end < len(items) else None

    return {
        "narrative": narrative,
        "window": window,
        "items": page,
        "nextCursor": next_cursor,
    }
