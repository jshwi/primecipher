"""API routes for refresh operations."""

import typing as t

from fastapi import APIRouter, Depends, Query

from ...deps.auth import require_refresh_token
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
