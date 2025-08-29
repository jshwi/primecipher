from fastapi import APIRouter, Query, Depends
from typing import Any, Dict
from ...parents import refresh_all, compute_all
from ...storage import mark_refreshed, last_refresh_ts
from ...deps.auth import require_refresh_token
from ...schemas import RefreshResp

router = APIRouter()

@router.post("/refresh", response_model=RefreshResp)
def refresh(
    window: str = Query(default="24h"),
    dryRun: bool = Query(default=False),
    _auth = Depends(require_refresh_token),
) -> Dict[str, Any]:
    if dryRun:
        items = compute_all()
        return {"ok": True, "window": window, "dryRun": True, "items": items, "ts": last_refresh_ts()}
    refresh_all()
    mark_refreshed()
    return {"ok": True, "window": window, "ts": last_refresh_ts()}
