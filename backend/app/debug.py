# backend/app/debug.py
from __future__ import annotations

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query

from .seeds import load_narrative_seeds
from .adapters.onchain import make_onchain_adapter
from .config import PROVIDER

router = APIRouter(tags=["debug"])


def _find_seed_parent(narrative: Optional[str], parent_symbol: str) -> Dict[str, Any] | None:
    """
    Locate a parent config inside the narrative seeds by its symbol, if a narrative is provided.
    """
    if not narrative:
        return None

    seeds = load_narrative_seeds()
    seed = next((s for s in seeds if s.get("narrative") == narrative), None)
    if not seed:
        return None

    parent_symbol = parent_symbol.upper()
    return next(
        (
            p
            for p in (seed.get("parents") or [])
            if (p.get("symbol") or "").upper() == parent_symbol
        ),
        None,
    )


@router.get("/children/{parent}")
def debug_children(
    parent: str,
    narrative: Optional[str] = Query(
        None, description="If provided, use seeds for terms/flags/blocklist"
    ),
    applyBlocklist: bool = Query(
        False, description="Apply seed blocklist to results"
    ),
    allowNameMatch: Optional[bool] = Query(
        None, description="Override seed nameMatchAllowed"
    ),
    dexIds: Optional[str] = Query(
        None, description="CSV override, e.g. raydium,orca,pump"
    ),
    volMinUsd: Optional[float] = Query(None),
    liqMinUsd: Optional[float] = Query(None),
    maxAgeHours: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(
        0, ge=0, description="Pagination offset applied after filtering/blocklist"
    ),
):
    """
    Probe child discovery for a parent symbol, with pagination and per-request discovery overrides.

    Notes:
    - `total` in counts is PRE-blocklist length (raw adapter results).
    - Pagination is applied AFTER blocklist/filtering so the UI can 'load more' intuitively.
    """
    parent_sym = parent.upper()
    seed_parent = _find_seed_parent(narrative, parent_sym)

    # Terms / flags from seeds, with optional overrides
    terms: List[str] = (seed_parent.get("match") if seed_parent else None) or [
        parent_sym.lower()
    ]
    allow_name = (
        allowNameMatch
        if allowNameMatch is not None
        else ((seed_parent.get("nameMatchAllowed", True)) if seed_parent else True)
    )
    block = (seed_parent.get("block") or []) if seed_parent else []
    discovery_seed = (seed_parent.get("discovery") or {}) if seed_parent else {}

    # Build per-request discovery overrides (kept minimal; adapter enforces defaults)
    discovery: Dict[str, Any] = dict(discovery_seed)
    if dexIds is not None:
        discovery["dexIds"] = [x.strip().lower() for x in dexIds.split(",") if x.strip()]
    if volMinUsd is not None:
        discovery["volMinUsd"] = float(volMinUsd)
    if liqMinUsd is not None:
        discovery["liqMinUsd"] = float(liqMinUsd)
    if maxAgeHours is not None:
        discovery["maxAgeHours"] = float(maxAgeHours)

    # Adapter (uses global HTTP_TIMEOUT/config internally)
    adapter = make_onchain_adapter(PROVIDER)

    # Fetch a superset so that post-filter pagination has enough headroom
    # We cap adapter limit at offset+limit up to 500 for safety.
    effective_limit = min(500, max(limit, offset + limit))

    children = adapter.fetch_children_for_parent(
        parent_symbol=parent_sym,
        match_terms=terms,
        allow_name_match=allow_name,
        limit=effective_limit,
        discovery=discovery,
    )

    total_pre_block = len(children)

    # Apply blocklist (if requested)
    if applyBlocklist and block:
        blocked = set(block)
        filtered = [c for c in children if (c.get("symbol") or "").upper() not in blocked]
    else:
        filtered = children

    # Apply pagination AFTER filtering
    page = filtered[offset : offset + limit]

    return {
        "resolved": {
            "parent": parent_sym,
            "narrative": narrative,
            "terms": terms,
            "allowNameMatch": allow_name,
            "block": block,
            "discovery": {
                "dexIds": discovery.get("dexIds"),
                "volMinUsd": discovery.get("volMinUsd"),
                "liqMinUsd": discovery.get("liqMinUsd"),
                "maxAgeHours": discovery.get("maxAgeHours"),
            },
        },
        "counts": {
            "total": total_pre_block,   # before blocklist
            "returned": len(page),      # after blocklist + pagination
            "offset": offset,
            "limit": limit,
        },
        "children": page,
    }

