from __future__ import annotations
import os, time, typing as t
from typing import List, Dict, Tuple
import random

from .registry import register_adapter, make_adapter, get_adapter_names

# Global TTL for raw provider results (seconds)
TTL_SEC = int(os.getenv("SOURCE_TTL", "60"))

# Shared raw cache across providers: (provider, normalized_terms) -> (ts, items)
_raw_cache: dict[Tuple[str, Tuple[str, ...]], Tuple[float, List[Dict]]] = {}
# Back-compat alias for older tests/helpers that expect `_cache`
_cache = _raw_cache

def _now() -> float:
    return time.time()

def _normalize_terms(terms: List[str]) -> Tuple[str, ...]:
    """Lowercase, strip, drop empties, unique, and sort for a stable cache key."""
    norm = {t.strip().lower() for t in (terms or []) if t and t.strip()}
    return tuple(sorted(norm))

def _get_raw_cached(key: Tuple[str, Tuple[str, ...]]) -> t.Optional[List[Dict]]:
    hit = _raw_cache.get(key)
    if not hit:
        return None
    ts, val = hit
    if _now() - ts > TTL_SEC:
        return None
    return val

def _set_raw_cached(key: Tuple[str, Tuple[str, ...]], val: List[Dict]) -> None:
    _raw_cache[key] = (_now(), val)

def _memo_raw(provider: str, terms: List[str], producer: t.Callable[[], List[Dict]]) -> List[Dict]:
    """
    Cache raw provider results per (provider, normalized terms).
    Narrative-dependent filtering must be applied *after* this memoization.
    """
    key = (provider, _normalize_terms(terms))
    cached = _get_raw_cached(key)
    if cached is not None:
        return cached
    val = producer() or []
    _set_raw_cached(key, val)
    return val

# --------------------------
# Local item producers (raw)
# --------------------------

def _deterministic_items(narrative: str, terms: List[str]) -> List[Dict]:
    base = terms or [narrative, "parent", "seed"]
    return [
        {"parent": f"{base[0]}-source-1", "matches": 11},
        {"parent": f"{base[min(1, len(base)-1)]}-source-2", "matches": 10},
        {"parent": f"{base[min(2, len(base)-1)]}-source-3", "matches": 9},
    ]

def _random_items(terms: List[str]) -> List[Dict]:
    n = random.randint(2, 6)
    out: List[Dict] = []
    for i in range(n):
        t0 = terms[i % len(terms)] if terms else f"parent{i}"
        out.append({"parent": f"{t0}-source-{i+1}", "matches": random.randint(3, 42)})
    out.sort(key=lambda x: -x["matches"])
    return out

# ---------------
# Seed semantics
# ---------------

def _apply_seed_semantics(
    narrative: str,
    terms: List[str],
    allow_name_match: bool,
    block: List[str] | None,
    items: List[Dict],
    require_all_terms: bool = False,
) -> List[Dict]:
    nl = (narrative or "").lower()
    term_list = [t.lower() for t in (terms or []) if t]
    block_list = [b.lower() for b in (block or []) if b]

    filtered: List[Dict] = []
    for it in items:
        p = str(it.get("parent", "")).lower()
        if any(b in p for b in block_list):
            continue
        if not allow_name_match and nl and nl in p:
            if not any(t_ in p for t_ in term_list if t_ != nl):
                continue
        if require_all_terms and term_list:
            if not all(t_ in p for t_ in term_list):
                continue
        filtered.append(it)

    filtered.sort(key=lambda x: -int(x.get("matches", 0)))
    return filtered[:3]  # small, stable lists for UI

# -------------------------
# Providers (registered)
# -------------------------

@register_adapter("test")
def _make_test():
    class _TestAdapter:
        def parents_for(self, narrative, terms, allow_name_match=True, block=None, require_all_terms=False):
            raw = _memo_raw("test", terms, lambda: _deterministic_items(narrative, terms))
            return _apply_seed_semantics(narrative, terms, allow_name_match, block or [], raw, require_all_terms)
    return _TestAdapter()

@register_adapter("dev")
def _make_dev():
    class _DevAdapter:
        def parents_for(self, narrative, terms, allow_name_match=True, block=None, require_all_terms=False):
            raw = _memo_raw("dev", terms, lambda: _random_items(terms))
            return _apply_seed_semantics(narrative, terms, allow_name_match, block or [], raw, require_all_terms)
    return _DevAdapter()

@register_adapter("coingecko")
def _make_cg():
    import httpx
    class _CGAdapter:
        def parents_for(self, narrative, terms, allow_name_match=True, block=None, require_all_terms=False):
            def _fetch():
                try:
                    q = " ".join(sorted(set([t for t in terms if t.strip()]))) or "sol"
                    url = "https://api.coingecko.com/api/v3/search"
                    with httpx.Client(timeout=6.0) as cl:
                        r = cl.get(url, params={"query": q})
                        r.raise_for_status()
                        js = r.json() or {}

                    coins = js.get("coins") or []
                    out: List[Dict] = []
                    for i, c in enumerate(coins[:8]):
                        name = c.get("name") or c.get("id") or f"cg-{i}"
                        rank = c.get("market_cap_rank") or 1000
                        score = max(3, 100 - int(rank))
                        out.append({"parent": name, "matches": score})
                    if not out:
                        out = _deterministic_items(q, terms)
                    out.sort(key=lambda x: -x["matches"])
                    return out[:3]
                except Exception:
                    # Any network/JSON/HTTP error → deterministic fallback
                    q = " ".join(sorted(set([t for t in terms if t.strip()]))) or "sol"
                    return _deterministic_items(q, terms)

            raw = _memo_raw("coingecko", terms, _fetch)
            return _apply_seed_semantics(narrative, terms, allow_name_match, block or [], raw, require_all_terms)
    return _CGAdapter()

# ---------------------------------
# Public façade (kept for callers)
# ---------------------------------

MODE = (os.getenv("SOURCE_MODE") or "dev").lower()

class Source:
    """Thin façade that delegates to the selected adapter from the registry."""
    def __init__(self, provider: str | None = None):
        self._name = (provider or MODE).lower()
        self._impl = make_adapter(self._name)

    @staticmethod
    def available() -> List[str]:
        return get_adapter_names()

    def parents_for(
        self,
        narrative: str,
        terms: List[str],
        allow_name_match: bool = True,
        block: List[str] | None = None,
        require_all_terms: bool = False,
    ) -> List[Dict]:
        return self._impl.parents_for(
            narrative,
            terms,
            allow_name_match=allow_name_match,
            block=block,
            require_all_terms=require_all_terms,
        )
