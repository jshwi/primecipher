"""API routes for narratives."""

import os
import time

from fastapi import APIRouter

from ...schemas import NarrativesResp
from ...seeds import list_narrative_names
from ...storage import get_meta, last_refresh_ts

router = APIRouter()

# TTL configuration for staleness checks
TTL_SEC = int(os.getenv("REFRESH_TTL_SEC", "900"))  # default 15m


def _get_last_job_errors() -> int:
    """Get the number of errors from the last completed refresh job.

    :return: Number of errors from the last job, or 0 if no job or no errors.
    """
    # Import here to avoid circular imports
    from .refresh import last_completed_job

    if not last_completed_job:
        return 0

    errors = last_completed_job.get("errors", [])
    return len(errors) if errors else 0


@router.get("/narratives", response_model=NarrativesResp)
def list_narratives() -> dict:
    """Get list of available narratives.

    :return: List of available narratives with stale status and last updated
        timestamp.
    """
    narrative_names = list_narrative_names()

    # Collect computedAt timestamps for all narratives
    computed_ats: list[float] = []
    for name in narrative_names:
        meta = get_meta(name)
        if meta and "computedAt" in meta:
            computed_ats.append(meta["computedAt"])

    # Calculate min and max computedAt
    min_computed_at = min(computed_ats) if computed_ats else None
    last_updated = max(computed_ats) if computed_ats else None

    # Determine if data is stale
    now = time.time()
    stale = (
        not computed_ats  # No narratives have been computed
        or min_computed_at is None  # No valid computedAt found
        or (now - min_computed_at) > TTL_SEC  # Any narrative is too old
        or _get_last_job_errors() > 0  # Last job had errors
    )

    return {
        "items": narrative_names,
        "lastRefresh": last_refresh_ts(),
        "stale": stale,
        "lastUpdated": last_updated,
    }
