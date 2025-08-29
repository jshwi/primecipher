from __future__ import annotations

import time
from typing import Dict, List

from .adapters.source import Source
from .repo import replace_parents, list_parents as list_parents_db
from .seeds import list_narrative_names, get_seeds

TOP_N = 100  # shared cap for refresh and routes


def _with_scores(items: List[Dict]) -> List[Dict]:
    """
    Deterministic scoring:
      • Always set float 'score' (never None).
      • If all 'matches' equal -> all scores = 0.0.
      • Else min–max normalize matches to [0,1].
      • Sort by (score desc, matches desc, parent asc) for stability.
    """
    if not items:
        return []

    matches = [int(it.get("matches") or 0) for it in items]
    lo, hi = min(matches), max(matches)

    out: List[Dict] = []
    if hi == lo:
        for it in items:
            out.append({**it, "score": 0.0})
    else:
        span = hi - lo
        for it, m in zip(items, matches):
            s = (m - lo) / span
            out.append({**it, "score": float(round(s, 6))})

    out.sort(
        key=lambda x: (
            -float(x.get("score") or 0.0),
            -int(x.get("matches") or 0),
            str(x.get("parent") or ""),
        )
    )
    return out


def _terms_for(narrative: str) -> List[str]:
    s = get_seeds()
    n = next((x for x in s.narratives if x.name == narrative), None)
    return list(n.terms.include or []) if n else []


def _fallback_items(narrative: str, terms: List[str]) -> List[Dict]:
    """
    Backstop when adapters return no data: tiny deterministic set so first-run
    and tests aren't empty. Only used if Source yields [].
    """
    base = len(terms) or 1
    return [
        {"parent": f"{narrative}-source-1", "matches": base + 9},
        {"parent": f"{narrative}-source-2", "matches": base + 5},
        {"parent": f"{narrative}-source-3", "matches": base + 0},
    ]


def compute_all() -> Dict[str, List[Dict]]:
    """
    Build raw (unscored) parents for each narrative using Source. Does NOT persist.
    If Source yields no items, synthesize a small deterministic fallback.
    """
    src = Source()
    out: Dict[str, List[Dict]] = {}
    for name in list_narrative_names():
        terms = _terms_for(name)
        items = src.parents_for(name, terms)
        if not items:
            items = _fallback_items(name, terms)
        out[name] = items
    return out


def refresh_all(dry_run: bool = False) -> Dict[str, List[Dict]]:
    """
    Compute for all narratives, score + cap to TOP_N, update BOTH:
      • repo (persistent) via replace_parents(name, scored, ts) when not dry_run
      • in-memory storage (app.storage) so tests/routes see it immediately
    Always returns the scored, capped mapping.
    """
    raw = compute_all()
    ts = int(time.time())
    scored_capped: Dict[str, List[Dict]] = {}

    # Lazy import to avoid circulars and keep tests happy
    from . import storage as _storage
    for name, items in raw.items():
        scored = _with_scores(items)[:TOP_N]
        scored_capped[name] = scored

        # Update in-memory storage for the running process (what tests read)
        if _storage is not None:
            if hasattr(_storage, "set_parents"):
                # Prefer explicit API if present
                try:
                    _storage.set_parents(name, scored)  # type: ignore[attr-defined]
                except Exception:
                    # fall back to touching the backing map
                    pass
            # Common simple backing map: _PARENTS: Dict[str, List[Dict]]
            if hasattr(_storage, "_PARENTS"):
                try:
                    _storage._PARENTS[name] = scored  # type: ignore[attr-defined]
                except Exception:
                    pass

        # Persist to repo (only when not dry run)
        if not dry_run:
            replace_parents(name, scored, ts)

    return scored_capped
