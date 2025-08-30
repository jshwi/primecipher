from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from ...deps.auth import require_refresh_token
from ...parents import compute_all, refresh_all
from ...schemas import RefreshResp
from ...storage import last_refresh_ts, mark_refreshed

router = APIRouter()


@router.post("/refresh", response_model=RefreshResp)
def refresh(
    window: str = Query(default="24h"),
    dryRun: bool = Query(default=False),
    _auth=Depends(require_refresh_token),
) -> dict[str, Any]:
    if dryRun:
        items = compute_all()
        return {
            "ok": True,
            "window": window,
            "dryRun": True,
            "items": items,
            "ts": last_refresh_ts(),
        }
    refresh_all()
    mark_refreshed()
    return {"ok": True, "window": window, "ts": last_refresh_ts()}
