"""API routes for refresh operations."""

import typing as t

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...deps.auth import require_refresh_token
from ...jobs import gc_jobs, get_job, start_refresh_job
from ...parents import compute_all, refresh_all
from ...schemas import RefreshResp
from ...storage import last_refresh_ts, mark_refreshed

router = APIRouter()


@router.post("/refresh", response_model=RefreshResp)
def refresh(
    window: str = Query(default="24h"),  # noqa: B008
    dry_run: bool = Query(default=False, alias="dryRun"),  # noqa: B008
    _auth=Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Refresh parent data for all narratives.

    :param window: The window to refresh.
    :param dry_run: Whether to run in dry run mode.
    :return: Refresh response.
    """
    if dry_run:
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


@router.post("/refresh/async")
async def refresh_async(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Start a background refresh.

    Returns { jobId } with 202 Accepted semantics.

    :return: Job ID.
    """

    async def _do() -> None:
        refresh_all()
        mark_refreshed()

    jid = await start_refresh_job(_do)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": jid}


@router.get("/refresh/status/{job_id}")
async def refresh_status(
    job_id: str,
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
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


@router.get("/refresh/status")
async def refresh_overview(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Get the status of a refresh job.

    :return: Status of the refresh job.
    """
    return {"running": False, "lastJob": None}
