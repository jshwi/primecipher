from fastapi import APIRouter, Depends, Query
from ...parents import refresh_all
from ...deps.auth import require_refresh_auth

router = APIRouter()

@router.post("/refresh")
def refresh(
    dryRun: bool = Query(default=False, alias="dryRun"),
    _auth: None = Depends(require_refresh_auth),
):
    items = refresh_all(dry_run=dryRun)
    return {"ok": True, "items": items, "dryRun": dryRun}
