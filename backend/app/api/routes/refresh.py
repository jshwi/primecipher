from fastapi import APIRouter, Query
from typing import Any, Dict
from ...parents import refresh_all, compute_all
from ...storage import mark_refreshed, last_refresh_ts

router = APIRouter()

@router.post("/refresh")
def refresh(window: str = Query(default="24h"), dryRun: bool = Query(default=False)) -> Dict[str, Any]:
    if dryRun:
        items = compute_all()
        # No persist, no mark_refreshed → ts unchanged
        return {"ok": True, "window": window, "dryRun": True, "items": items, "ts": last_refresh_ts()}
    refresh_all()
    mark_refreshed()
    return {"ok": True, "window": window, "ts": last_refresh_ts()}
