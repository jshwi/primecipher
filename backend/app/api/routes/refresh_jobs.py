from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict
from ...deps.auth import require_refresh_token
from ...jobs import start_refresh_job, get_job, gc_jobs
from ...parents import refresh_all
from ...storage import mark_refreshed

router = APIRouter()

@router.post("/refresh/async")
async def refresh_async(_auth = Depends(require_refresh_token)) -> Dict[str, Any]:
    """
    Start a background refresh. Returns { jobId } with 202 Accepted semantics.
    """
    async def _do():
        refresh_all()
        mark_refreshed()
    jid = await start_refresh_job(_do)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": jid}

@router.get("/refresh/status/{jobId}")
def refresh_status(jobId: str, _auth = Depends(require_refresh_token)) -> Dict[str, Any]:
    j = get_job(jobId)
    if not j:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown job")
    return j
