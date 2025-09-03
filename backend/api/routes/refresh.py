"""API routes for refresh operations."""

import time
import typing as t
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...deps.auth import require_refresh_token
from ...jobs import gc_jobs
from ...parents import compute_all, refresh_all
from ...storage import last_refresh_ts, mark_refreshed

router = APIRouter()

# Idempotency configuration
DEBOUNCE_SEC = 2

# Module-level registry for idempotency
current_running_job: dict[str, t.Any] | None = None
last_completed_job: dict[str, t.Any] | None = None
last_started_ts: float = 0.0


def _gen_id() -> str:
    """Generate a short job ID."""
    return uuid.uuid4().hex[:12]


def _get_job_by_id(job_id: str) -> dict[str, t.Any] | None:
    """Get job by ID from the module-level registry.

    :param job_id: The job ID to look up.
    :return: Job dictionary or None if not found.
    """
    if current_running_job and current_running_job.get("id") == job_id:
        return current_running_job
    if last_completed_job and last_completed_job.get("id") == job_id:
        return last_completed_job
    return None


async def start_or_get_job(
    mode: str = "dev",  # pylint: disable=unused-argument
    window: str = "24h",  # pylint: disable=unused-argument
) -> dict[str, t.Any]:
    """Start a new job or return existing job for idempotency.

    :param mode: The mode for the job (currently unused but kept for
        compatibility).
    :param window: The window for the job (currently unused but kept for
        compatibility).
    :return: Job dictionary with id, state, ts, error, and jobId fields.
    """
    # pylint: disable=global-statement
    global current_running_job, last_started_ts

    now = time.time()

    # If current_running_job exists and state=="running": return it
    if current_running_job and current_running_job.get("state") == "running":
        return current_running_job

    # If current_running_job exists and is completed/error AND within debounce
    # window: return it
    if (
        current_running_job
        and current_running_job.get("state") in ("done", "error")
        and (now - last_started_ts) < DEBOUNCE_SEC
    ):
        return current_running_job

    # If current_running_job exists but debounce window has expired, clear it
    if (
        current_running_job
        and current_running_job.get("state") in ("done", "error")
        and (now - last_started_ts) >= DEBOUNCE_SEC
    ):
        current_running_job = None

    # Else create new job
    job_id = _gen_id()
    new_job = {
        "id": job_id,
        "state": "running",
        "ts": now,
        "error": None,
        "jobId": job_id,  # Include jobId mirror in response
    }

    # Update global state
    current_running_job = new_job
    last_started_ts = now

    # Start the actual refresh job
    async def _do() -> None:
        # pylint: disable=global-statement
        global current_running_job, last_completed_job
        try:
            refresh_all()
            mark_refreshed()
            # Mark as completed
            completed_job = {
                "id": job_id,
                "state": "done",
                "ts": time.time(),
                "error": None,
                "jobId": job_id,
            }
            last_completed_job = completed_job
            # Keep current_running_job as completed for debounce window
            current_running_job = completed_job
        except Exception as e:
            # Mark as error
            error_job = {
                "id": job_id,
                "state": "error",
                "ts": time.time(),
                "error": str(e),
                "jobId": job_id,
            }
            last_completed_job = error_job
            # Keep current_running_job as error for debounce window
            current_running_job = error_job
            raise

    # Start the job in the background
    import asyncio

    asyncio.create_task(_do())

    return new_job


@router.post("/refresh")
async def refresh(
    window: str = Query(default="24h"),  # noqa: B008
    dry_run: bool = Query(default=False, alias="dryRun"),  # noqa: B008
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Refresh parent data for all narratives.

    For dry run mode, returns legacy format with items.
    For normal mode, returns { jobId } with 202 Accepted semantics.

    :param window: The window to refresh.
    :param dry_run: Whether to run in dry run mode.
    :return: Refresh response or Job ID.
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

    # Use the same function as /refresh/async to ensure consistent behavior
    job = await start_or_get_job(mode="dev", window=window)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": job["jobId"]}


@router.post("/refresh/async")
async def refresh_async(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Start a background refresh.

    Returns { jobId } with 202 Accepted semantics.
    If a job is already running, returns the same job ID.

    :return: Job ID.
    """
    job = await start_or_get_job()
    return {"jobId": job["jobId"]}


@router.get("/refresh/status/{job_id}")
async def refresh_status(
    job_id: str,
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Get status of a refresh job.

    :param job_id: The ID of the job to get status for.
    :return: Job status.
    """
    j = _get_job_by_id(job_id)
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
    """Get the status of refresh jobs.

    :return: Status of refresh jobs - either running job or last finished job.
    """
    # Use the new module-level registry
    if current_running_job and current_running_job.get("state") == "running":
        return {"running": True, **current_running_job}

    return {
        "running": False,
        "lastJob": last_completed_job,
    }
