"""API routes for parents data."""

import base64
import json
import typing as t

from fastapi import APIRouter, HTTPException, Path, Query

from ...parents import TOP_N, _with_scores
from ...repo import list_parents as list_parents_db
from ...schemas import ParentsResp
from ...seeds import list_narrative_names
from ...storage import get_parents

router = APIRouter()


def _enc_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(
        json.dumps({"o": offset}).encode(),
    ).decode()


def _dec_cursor(cursor: str) -> int:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        if "o" not in data:
            raise ValueError("missing 'o' field")
        off = int(data["o"])
        if off < 0:
            raise ValueError("negative offset")
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
    limit: int = Query(default=25),  # noqa: B008
    cursor: str | None = Query(default=None),  # noqa: B008
    debug: bool = Query(default=False),  # noqa: B008
) -> dict[str, t.Any]:
    """Get parents data for a narrative with pagination.

    :param narrative: The narrative to get parents data for.
    :param window: The window to get parents data for.
    :param limit: The limit of parents data to get.
    :param cursor: The cursor to get parents data for.
    :param debug: Whether to include debug fields like sources.
    :return: Parents data.
    """
    if narrative not in set(list_narrative_names()):
        raise HTTPException(status_code=404, detail="unknown narrative")

    # load & score
    items = list_parents_db(narrative) or get_parents(narrative)
    items = _with_scores(items)[:TOP_N]  # keep consistent with compute_all cap

    # clamp limit to 1..100 range
    limit = max(1, min(100, limit))

    # decode cursor -> start offset
    start = _dec_cursor(cursor) if cursor else 0

    # if start offset >= len(items), return empty page
    if start >= len(items):
        return {
            "narrative": narrative,
            "window": window,
            "items": [],
            "nextCursor": None,
        }

    end = min(start + limit, len(items))
    page = items[start:end]

    # Filter out debug fields if not in debug mode
    if not debug:
        for item in page:
            item.pop("sources", None)

    next_cursor = _enc_cursor(end) if end < len(items) else None

    return {
        "narrative": narrative,
        "window": window,
        "items": page,
        "nextCursor": next_cursor,
    }
