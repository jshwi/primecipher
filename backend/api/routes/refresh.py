"""API routes for refresh operations."""

import logging
import os
import time
import typing as t
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...adapters.source import get_cg_calls_count, reset_cg_calls_count
from ...deps.auth import require_refresh_token
from ...jobs import gc_jobs
from ...parents import compute_all, refresh_all
from ...seeds import list_narrative_names
from ...storage import get_parents, last_refresh_ts, mark_refreshed

router = APIRouter()

# Idempotency configuration
DEBOUNCE_SEC = 2

# TTL configuration for staleness checks
TTL_SEC = int(os.getenv("REFRESH_TTL_SEC", "900"))  # default 15m

# Budget control configuration
REFRESH_MAX_CALLS = int(os.getenv("REFRESH_MAX_CALLS", "50"))
REFRESH_PER_NARRATIVE_CAP = int(os.getenv("REFRESH_PER_NARRATIVE_CAP", "1"))

# Module-level registry for idempotency
current_running_job: dict[str, t.Any] | None = None
last_completed_job: dict[str, t.Any] | None = None
last_started_ts: float = 0.0
debounce_until: float = 0.0
last_success_at: float = 0.0


def _get_narrative_count() -> int:
    """Get the total number of narratives from seeds.

    :return: Total number of narratives.
    """
    return len(list_narrative_names())


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


def _process_narrative_dev_mode(narrative: str) -> list[dict]:
    """Process a single narrative in dev mode.

    :param narrative: The narrative name to process.
    :return: List of parent items for the narrative.
    """
    # Import here to avoid circular imports
    from ... import parents as parents_module

    # Detect compute function using introspection
    comp = getattr(parents_module, "compute_parents", None) or getattr(
        parents_module,
        "for_narrative",
        None,
    )

    if comp is not None:
        # Use the detected compute function
        items = comp(narrative)
    else:
        # Fall back to getting current stored items to simulate refresh
        items = get_parents(narrative) or []

    return items


def _process_narrative_real_mode(
    narrative: str,
    terms: list[str],
    mode: str = "real",
) -> list[dict]:
    """Process a single narrative in real mode using adapter.

    :param narrative: The narrative name to process.
    :param terms: List of search terms for the narrative.
    :param mode: The mode to determine which adapter to use.
    :return: List of parent items for the narrative.
    """
    from ...adapters import get_adapter

    # Get the appropriate adapter based on mode
    adapter = get_adapter(mode)

    # Fetch parents using the adapter
    items = adapter.fetch_parents(narrative, terms)

    return items


def _check_budget_limits(
    narrative: str,
    mode: str = "real",
    narratives_done: int = 0,
) -> tuple[bool, dict[str, str] | None]:
    """Check if budget limits are exceeded.

    :param narrative: Current narrative being processed.
    :param mode: The processing mode to determine call cost.
    :param narratives_done: Number of narratives already processed.
    :return: Tuple of (should_continue, error_dict_or_none).
    """
    # Get current calls from source module
    calls_used = get_cg_calls_count()

    # Determine calls needed for this narrative
    calls_needed = 2 if mode == "real_mix" else 1

    # Check if we would exceed the maximum calls budget
    if calls_used + calls_needed > REFRESH_MAX_CALLS:
        budget_error = {
            "narrative": "*",
            "code": "BUDGET_EXCEEDED",
            "detail": "max calls exceeded",
        }
        return False, budget_error

    # Check per-narrative cap
    if 0 < REFRESH_PER_NARRATIVE_CAP <= narratives_done:
        budget_error = {
            "narrative": narrative,
            "code": "BUDGET_EXCEEDED",
            "detail": "per-narrative cap",
        }
        return True, budget_error  # Continue but skip this narrative

    return True, None  # Continue processing


def _process_single_narrative(
    narrative: str,
    job_id: str,  # pylint: disable=unused-argument
    mode: str = "dev",
    terms: list[str] | None = None,
    _memo: dict | None = None,
) -> tuple[bool, dict | None]:
    """Process a single narrative and return results.

    :param narrative: The narrative to process.
    :param job_id: The job ID.
    :param mode: The processing mode (dev or real).
    :param terms: List of search terms for real mode.
    :param _memo: Per-run memo dict for caching results.
    :return: Tuple of (success, error_dict_or_none).
    """
    try:
        # Check if we have cached results in memo
        if _memo is not None and narrative in _memo:
            items = _memo[narrative]
        else:
            # Process the narrative based on mode
            if mode in ["real", "real_cg", "real_mix"] and terms is not None:
                items = _process_narrative_real_mode(narrative, terms, mode)
            else:
                items = _process_narrative_dev_mode(narrative)

            # Cache the results in memo
            if _memo is not None:
                _memo[narrative] = items

        # Write to storage
        _write_narrative_to_storage(narrative, items)

        # Small non-blocking yield to make progress visible
        time.sleep(0.05)

        return True, None

    except (ValueError, RuntimeError, OSError) as e:
        error_entry = {
            "narrative": narrative,
            "code": "PROCESSING_ERROR",
            "detail": str(e),
        }
        return False, error_entry


def _update_job_progress(
    job_id: str,
    narratives_done: int,
    errors: list[dict],
) -> None:
    """Update job progress in the global state.

    :param job_id: The job ID.
    :param narratives_done: Number of narratives completed.
    :param errors: List of errors.
    """
    if current_running_job and current_running_job.get("id") == job_id:
        current_running_job["narrativesDone"] = narratives_done
        current_running_job["calls_used"] = get_cg_calls_count()
        current_running_job["errors"] = errors


def _write_narrative_to_storage(narrative: str, items: list[dict]) -> None:
    """Write narrative items to storage and database.

    :param narrative: The narrative name.
    :param items: The items to write.
    """
    from ... import storage as storage_module
    from ...repo import replace_parents

    # Use set_parents which automatically records computedAt timestamp
    writer = getattr(storage_module, "set_parents", None)

    if writer is not None:
        writer(narrative, items)

        # Transform items for database storage (needs 'parent' and 'matches')
        db_items = []
        for item in items:
            db_item = {
                "parent": item.get("name", item.get("parent", "unknown")),
                "matches": int(item.get("matches", 0)),
            }
            db_items.append(db_item)

        # Also write to database for API consistency
        replace_parents(narrative, db_items, time.time())
    else:
        raise RuntimeError(
            "No storage writer found (set_parents)",
        )


def _process_narrative_real_cg(
    narrative: str,
    terms: list[str],
    _memo: dict[str, list[dict]],
    job_id: str,
) -> tuple[bool, list[dict]]:
    """Process a narrative in real_cg mode with memo and budget checking.

    :param narrative: The narrative name.
    :param terms: List of search terms.
    :param _memo: Per-run memo dict for caching results.
    :param job_id: The job ID.
    :return: Tuple of (should_continue, items).
    """
    if narrative in _memo:
        # Use cached results from memo
        items = _memo[narrative]
        return True, items

    # Check budget before making API call
    calls_used = get_cg_calls_count()
    if calls_used + 1 > REFRESH_MAX_CALLS:
        return False, []

    # Fetch data using CoinGeckoAdapter
    from ...adapters import get_adapter

    adapter = get_adapter("real_cg")
    items = adapter.fetch_parents(narrative, terms)
    _memo[narrative] = items

    # Update progress in global job state
    if current_running_job and current_running_job.get("id") == job_id:
        current_running_job["calls_used"] = get_cg_calls_count()

    return True, items


def _create_completed_job(  # pylint: disable=too-many-positional-arguments
    job_id: str,
    mode: str,
    window: str,
    narratives_total: int,
    narratives_done: int,
    errors: list[dict],
    reason: str | None = None,
) -> dict[str, t.Any]:
    """Create a completed job dictionary.

    :param job_id: The job ID.
    :param mode: The job mode.
    :param window: The job window.
    :param narratives_total: Total number of narratives.
    :param narratives_done: Number of narratives completed.
    :param errors: List of errors.
    :param reason: Optional reason for completion.
    :return: Completed job dictionary.
    """
    job = {
        "id": job_id,
        "state": "done",
        "ts": time.time(),
        "error": None,
        "jobId": job_id,
        "mode": mode,
        "window": window,
        "narrativesTotal": narratives_total,
        "narrativesDone": narratives_done,
        "errors": errors,
        "calls_used": get_cg_calls_count(),
    }
    if reason:
        job["reason"] = reason
    return job


def _finalize_job(  # pylint: disable=too-many-positional-arguments
    job_id: str,
    mode: str,
    window: str,
    narratives_total: int,
    narratives_done: int,
    errors: list[dict],
    reason: str | None = None,
) -> None:
    """Finalize a job by marking it as completed.

    :param job_id: The job ID.
    :param mode: The job mode.
    :param window: The job window.
    :param narratives_total: Total number of narratives.
    :param narratives_done: Number of narratives completed.
    :param errors: List of errors.
    :param reason: Optional reason for completion.
    """
    # pylint: disable=global-statement
    global current_running_job, last_completed_job, debounce_until
    global last_success_at

    mark_refreshed()
    completed_job = _create_completed_job(
        job_id=job_id,
        mode=mode,
        window=window,
        narratives_total=narratives_total,
        narratives_done=narratives_done,
        errors=errors,
        reason=reason,
    )
    last_completed_job = completed_job
    # Update last success timestamp
    last_success_at = completed_job["ts"]
    # Set debounce_until BEFORE clearing current_running_job
    debounce_until = time.time() + DEBOUNCE_SEC
    current_running_job = None


def _process_dev_mode_job(
    job_id: str,
    mode: str,
    window: str,
    narratives_total: int,
) -> None:
    """Process a job by iterating through narratives.

    :param job_id: The job ID.
    :param mode: The job mode (dev or real).
    :param window: The job window.
    :param narratives_total: Total number of narratives to process.
    """
    # pylint: disable=global-statement,too-many-locals
    global current_running_job, last_completed_job, debounce_until

    try:
        # Reset CG calls counter at start of job
        reset_cg_calls_count()

        # Per-run memo: dict to cache computed parents by narrative
        _memo: dict[str, list[dict]] = {}

        # Get narratives with their terms for real mode
        if mode in ["real", "real_cg", "real_mix"]:
            from ...seeds import load_seeds

            seeds_data = load_seeds()
            narratives_with_terms = [
                (n["name"], n.get("terms", []))
                for n in seeds_data["narratives"]
            ]
        else:
            narratives_with_terms = [
                (name, []) for name in list_narrative_names()
            ]

        narratives_done = 0
        errors = []

        for narrative, terms in narratives_with_terms:
            # Special handling for real_cg mode with per-run memo and budget
            if mode == "real_cg":
                should_continue, items = _process_narrative_real_cg(
                    narrative,
                    terms,
                    _memo,
                    job_id,
                )

                if not should_continue:
                    # Budget exceeded - add error and finalize
                    budget_error = {
                        "narrative": "*",
                        "code": "BUDGET_EXCEEDED",
                        "detail": "max calls exceeded",
                    }
                    errors.append(budget_error)
                    _finalize_job(
                        job_id=job_id,
                        mode=mode,
                        window=window,
                        narratives_total=narratives_total,
                        narratives_done=narratives_done,
                        errors=errors,
                        reason="budget_exhausted",
                    )
                    return  # Exit the function early

                # Log before writing to storage
                logging.info(
                    "[REFRESH] %s parents_in=%s",
                    narrative,
                    len(items),
                )

                # Write to storage using current storage writer
                _write_narrative_to_storage(narrative, items)
                narratives_done += 1
                _update_job_progress(
                    job_id,
                    narratives_done,
                    errors,
                )
                continue

            # Check budget limits for other modes
            should_continue_other, budget_error_other = _check_budget_limits(
                narrative,
                mode,
                narratives_done,
            )

            if budget_error_other:
                errors.append(budget_error_other)
                if not should_continue_other:
                    # Budget exceeded - finalize and break
                    _finalize_job(
                        job_id=job_id,
                        mode=mode,
                        window=window,
                        narratives_total=narratives_total,
                        narratives_done=narratives_done,
                        errors=errors,
                        reason="budget_exhausted",
                    )
                    return  # Exit the function early
                # Skip this narrative and continue with next
                narratives_done += 1
                _update_job_progress(
                    job_id,
                    narratives_done,
                    errors,
                )
                continue

            # Process the narrative for other modes
            _, error_entry = _process_single_narrative(
                narrative,
                job_id,
                mode=mode,
                terms=(
                    terms if mode in ["real", "real_cg", "real_mix"] else None
                ),
                _memo=_memo,
            )

            narratives_done += 1

            if error_entry:
                errors.append(error_entry)

            _update_job_progress(job_id, narratives_done, errors)

        # Mark as completed
        _finalize_job(
            job_id=job_id,
            mode=mode,
            window=window,
            narratives_total=narratives_total,
            narratives_done=narratives_done,
            errors=errors,
        )

    except (ValueError, RuntimeError, OSError) as e:
        # Mark as error
        error_entry = {"narrative": "*", "code": "JOB_ERROR", "detail": str(e)}
        error_job = {
            "id": job_id,
            "state": "error",
            "ts": time.time(),
            "error": str(e),
            "jobId": job_id,
            "mode": mode,
            "window": window,
            "narrativesTotal": narratives_total,
            "narrativesDone": 0,
            "errors": [error_entry],
            "calls_used": get_cg_calls_count(),
        }
        last_completed_job = error_job
        # Set debounce_until BEFORE clearing current_running_job
        debounce_until = time.time() + DEBOUNCE_SEC
        current_running_job = None
        raise


async def start_or_get_job(
    mode: str = "prod",  # pylint: disable=unused-argument
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
    global current_running_job

    now = time.time()

    # 1) If current_running_job and state=="running": return it
    if current_running_job and current_running_job.get("state") == "running":
        return current_running_job

    # 2) If now < debounce_until: return last_completed_job
    # (and include "jobId" mirror)
    if now < debounce_until and last_completed_job:
        return last_completed_job

    # 3) Else create a new job (id, ts, state="running"), immediately finish it
    # (Step-2 behavior), set last_completed_job = new_job,
    # debounce_until = now + DEBOUNCE_SEC, current_running_job = None.
    # Return new_job (and include "jobId").
    job_id = _gen_id()
    narratives_total = _get_narrative_count()
    new_job = {
        "id": job_id,
        "state": "running",
        "ts": now,
        "error": None,
        "jobId": job_id,  # Include jobId mirror in response
        "mode": mode,
        "window": window,
        "narrativesTotal": narratives_total,
        "narrativesDone": 0,
        "errors": [],
        "calls_used": 0,
    }

    # Update global state
    current_running_job = new_job

    # Start the actual refresh job
    async def _do() -> None:
        if mode in ["dev", "real", "real_cg", "real_mix"]:
            # Use new processing for dev and real modes
            _process_dev_mode_job(job_id, mode, window, narratives_total)
        else:
            # Use existing refresh_all() for other modes (like prod)
            # pylint: disable=global-statement
            global current_running_job, last_completed_job, debounce_until
            try:
                refresh_all()
                mark_refreshed()
                # Mark as completed
                completed_ts = time.time()
                completed_job = {
                    "id": job_id,
                    "state": "done",
                    "ts": completed_ts,
                    "error": None,
                    "jobId": job_id,
                    "mode": mode,
                    "window": window,
                    "narrativesTotal": narratives_total,
                    "narrativesDone": narratives_total,
                    "errors": [],
                    "calls_used": get_cg_calls_count(),
                }
                last_completed_job = completed_job
                # Update last success timestamp
                # pylint: disable=global-statement
                global last_success_at
                last_success_at = completed_ts
                # Set debounce_until BEFORE clearing current_running_job
                debounce_until = time.time() + DEBOUNCE_SEC
                current_running_job = None
            except (ValueError, RuntimeError, OSError) as e:
                # Mark as error
                error_entry = {
                    "narrative": "*",
                    "code": "JOB_ERROR",
                    "detail": str(e),
                }
                error_job = {
                    "id": job_id,
                    "state": "error",
                    "ts": time.time(),
                    "error": str(e),
                    "jobId": job_id,
                    "mode": mode,
                    "window": window,
                    "narrativesTotal": narratives_total,
                    "narrativesDone": 0,
                    "errors": [error_entry],
                    "calls_used": get_cg_calls_count(),
                }
                last_completed_job = error_job
                # Set debounce_until BEFORE clearing current_running_job
                debounce_until = time.time() + DEBOUNCE_SEC
                current_running_job = None
                raise

    # Start the job in the background
    import asyncio

    asyncio.create_task(_do())

    return new_job


@router.post("/refresh")
async def refresh(
    window: str = Query(default="24h"),  # noqa: B008
    dry_run: bool = Query(default=False, alias="dryRun"),  # noqa: B008
    mode: str = Query(default="prod"),  # noqa: B008
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Refresh parent data for all narratives.

    For dry run mode, returns legacy format with items.
    For normal mode, returns { jobId } with 202 Accepted semantics.

    :param window: The window to refresh.
    :param dry_run: Whether to run in dry run mode.
    :param mode: The mode for the refresh (dev or other).
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
    job = await start_or_get_job(mode=mode, window=window)
    gc_jobs()  # opportunistic cleanup
    return {"jobId": job["jobId"]}


@router.post("/refresh/async")
async def refresh_async(
    mode: str = Query(default="prod"),  # noqa: B008
    window: str = Query(default="24h"),  # noqa: B008
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Start a background refresh.

    Returns { jobId } with 202 Accepted semantics.
    If a job is already running, returns the same job ID.

    :param mode: The mode for the refresh (dev or other).
    :param window: The window for the refresh.
    :return: Job ID.
    """
    job = await start_or_get_job(mode=mode, window=window)
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

    # Add budget information to the response
    response = j.copy()
    response["max_calls"] = REFRESH_MAX_CALLS
    response["per_narrative_cap"] = REFRESH_PER_NARRATIVE_CAP
    return response


@router.get("/refresh/status")
async def refresh_overview(
    _auth: t.Any = Depends(require_refresh_token),  # noqa: B008
) -> dict[str, t.Any]:
    """Get the status of refresh jobs.

    :return: Status of refresh jobs - either running job or last finished job.
    """
    # Use the new module-level registry
    if current_running_job and current_running_job.get("state") == "running":
        response = {"running": True, **current_running_job}
        if last_success_at > 0:
            response["lastSuccessAt"] = last_success_at
        # Add budget information
        response["max_calls"] = REFRESH_MAX_CALLS
        response["per_narrative_cap"] = REFRESH_PER_NARRATIVE_CAP
        return response

    response = {
        "running": False,
        "lastJob": last_completed_job,
    }
    if last_success_at > 0:
        response["lastSuccessAt"] = last_success_at
    # Add budget information
    response["max_calls"] = REFRESH_MAX_CALLS
    response["per_narrative_cap"] = REFRESH_PER_NARRATIVE_CAP
    return response
