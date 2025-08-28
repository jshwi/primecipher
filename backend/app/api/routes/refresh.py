
from fastapi import APIRouter, Query
from typing import Any, Dict
from ...parents import refresh_all
from ...storage import mark_refreshed, last_refresh_ts

router = APIRouter()

@router.post("/refresh")
def refresh(window: str = Query(default="24h")) -> Dict[str, Any]:
    refresh_all()
    mark_refreshed()
    return {"ok": True, "window": window, "ts": last_refresh_ts()}
