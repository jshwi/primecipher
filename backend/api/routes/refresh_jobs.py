"""API routes for asynchronous refresh jobs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ...deps.auth import require_refresh_token
from ...jobs import gc_jobs, get_job, start_refresh_job
from ...parents import refresh_all
from ...storage import mark_refreshed

router = APIRouter()


@router.post("/refresh/async")
async def refresh_async(
    _auth=Depends(require_refresh_token),  # noqa: B008
) -> dict[str, Any]:
    """Start a background refresh.

    Returns { jobId } with 202 Accepted semantics.

    :return: Job ID.
    """

    async def _do():
        refresh_all()
        mark_refreshed()

    jid = await start_refresh_job(_do)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": jid}


@router.get("/refresh/status/{job_id}")
def refresh_status(
    job_id: str,
    _auth=Depends(require_refresh_token),  # noqa: B008
) -> dict[str, Any]:
    """Get status of a refresh job.

    :param job_id: The ID of the job to get status for.
    :return: Job status.
    """
    j = get_job(job_id)
    if not j:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unknown job",
        )
    return j
