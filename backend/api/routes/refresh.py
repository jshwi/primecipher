"""API routes for refresh operations."""

import os
import time
import typing as t

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ...deps.auth import require_refresh_token
from ...jobs import gc_jobs, get_job, start_refresh_job
from ...parents import compute_all, refresh_all
from ...schemas import JobState, RefreshResp
from ...storage import last_refresh_ts, mark_refreshed

router = APIRouter()

# In-memory job state tracker
_job_state: JobState | None = None
DEFAULT_SEEDS_PATH = "/app/seeds/narratives.seed.json"


def _get_narratives_total() -> int:
    """Get total number of narratives from seeds.

    :return: Total number of narratives.
    """
    import json

    with open(
        os.getenv("SEEDS_FILE", DEFAULT_SEEDS_PATH),
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        return len(data.get("narratives", []))


def _create_job_id() -> str:
    """Create a timestamp-based job ID.

    :return: Job ID string.
    """
    return str(int(time.time()))


@router.post("/refresh", response_model=RefreshResp)
def refresh(
    mode: str = Query(default="dev"),  # noqa: B008
    window: str = Query(default="24h"),  # noqa: B008
    dry_run: bool = Query(default=False, alias="dryRun"),  # noqa: B008
    _auth=Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Refresh parent data for all narratives.

    :param mode: The refresh mode.
    :param window: The window to refresh.
    :param dry_run: Whether to run in dry run mode.
    :return: Refresh response.
    """
    global _job_state

    if dry_run:
        items = compute_all()
        return {
            "ok": True,
            "window": window,
            "dryRun": True,
            "items": items,
            "ts": last_refresh_ts(),
        }

    # Check if job is already running
    if _job_state and _job_state.running:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=_job_state.model_dump(),
        )

    # Start new job
    job_id = _create_job_id()
    _job_state = JobState(
        jobId=job_id,
        running=True,
        startedAt=time.time(),
        mode=mode,
        window=window,
        narrativesTotal=_get_narratives_total(),
        narratives_done=0,
        errors=[],
    )

    # Do the actual work synchronously (for backward compatibility)
    try:
        refresh_all()
        mark_refreshed()

        # Update job state to completed
        _job_state.running = False
        _job_state.narratives_done = _job_state.narrativesTotal

        # Return original response format for backward compatibility
        return {"ok": True, "window": window, "ts": last_refresh_ts()}

    except Exception as e:
        # Update job state to error
        _job_state.running = False
        _job_state.errors.append(str(e))
        raise


@router.post("/refresh/async")
async def refresh_async(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Start a background refresh.

    Returns { jobId } with 202 Accepted semantics.
    If a job is already running, returns the same job ID.

    :return: Job ID.
    """
    from ...jobs import _LOCK, JOBS

    # Check if there's already a running or queued job
    async with _LOCK:
        for job_id, job in JOBS.items():
            if job.state in ("running", "queued"):
                return {"jobId": job_id, "id": job_id}

    async def _do() -> None:
        import asyncio

        await asyncio.sleep(0.1)  # Small delay to allow testing
        refresh_all()
        mark_refreshed()

    jid = await start_refresh_job(_do)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": jid, "id": jid}


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
    # Add jobId field alongside existing id field
    j["jobId"] = j["id"]
    return j


@router.get("/refresh/status")
async def refresh_overview(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Get the status of a refresh job.

    :return: Status of the refresh job.
    """
    if _job_state and _job_state.running:
        return _job_state.model_dump()

    return {
        "running": False,
        "lastJob": _job_state.model_dump() if _job_state else None,
    }
