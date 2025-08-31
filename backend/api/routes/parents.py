"""API routes for parents data."""

import base64
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query

from ...parents import TOP_N, _with_scores
from ...repo import list_parents as list_parents_db
from ...schemas import ParentsResp
from ...seeds import list_narrative_names
from ...storage import get_parents

router = APIRouter()


def _enc_cursor(offset: int) -> str:
    """Encode cursor with offset."""
    return base64.urlsafe_b64encode(
        json.dumps({"o": offset}).encode(),
    ).decode()


def _dec_cursor(cursor: str) -> int:
    """Decode cursor to get offset."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        off = int(data.get("o", 0))
        if off < 0:
            raise ValueError
        return off
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid cursor") from exc


@router.get(
    "/parents/{narrative}",
    response_model=ParentsResp,
    # ensure fastapi doesn't drop none fields like nextcursor at end of
    # list
    response_model_exclude_none=False,
    response_model_exclude_unset=False,
)
def get_parents_for_narrative(
    narrative: str = Path(..., min_length=1),  # noqa: B008
    window: str = Query(default="24h"),  # noqa: B008
    limit: int = Query(default=25, ge=1, le=100),  # noqa: B008
    cursor: str | None = Query(default=None),  # noqa: B008
) -> dict[str, Any]:
    """Get parents data for a narrative with pagination.

    :param narrative: The narrative to get parents data for.
    :param window: The window to get parents data for.
    :param limit: The limit of parents data to get.
    :param cursor: The cursor to get parents data for.
    :return: Parents data.
    """
    if narrative not in set(list_narrative_names()):
        raise HTTPException(status_code=404, detail="unknown narrative")

    # load & score
    items = list_parents_db(narrative) or get_parents(narrative)
    items = _with_scores(items)[:TOP_N]  # keep consistent with compute_all cap

    # decode cursor -> start offset
    start = _dec_cursor(cursor) if cursor else 0
    end = min(start + limit, len(items))
    page = items[start:end]

    next_cursor = _enc_cursor(end) if end < len(items) else None

    return {
        "narrative": narrative,
        "window": window,
        "items": page,
        "nextCursor": next_cursor,
    }
