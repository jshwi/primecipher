import os, time
from typing import List, Dict, Tuple

import typing as t

MODE = (os.getenv("SOURCE_MODE") or "dev").lower()
TTL_SEC = int(os.getenv("SOURCE_TTL", "60"))

_cache: dict[Tuple[str, Tuple[str, ...]], Tuple[float, List[Dict]]] = {}

def _get_cached(key: Tuple[str, Tuple[str, ...]]) -> t.Optional[List[Dict]]:
    now = time.time()
    hit = _cache.get(key)
    if not hit:
        return None
    ts, val = hit
    if now - ts > TTL_SEC:
        return None
    return val

def _set_cached(key: Tuple[str, Tuple[str, ...]], val: List[Dict]) -> None:
    _cache[key] = (time.time(), val)

def _deterministic_items(narrative: str, terms: List[str]) -> List[Dict]:
    base = terms or [narrative, "parent", "seed"]
    return [
        {"parent": f"{base[0]}-source-1", "matches": 11},
        {"parent": f"{base[min(1, len(base)-1)]}-source-2", "matches": 10},
        {"parent": f"{base[min(2, len(base)-1)]}-source-3", "matches": 9},
    ]

def _random_items(terms: List[str]) -> List[Dict]:
    import random
    n = random.randint(2, 6)
    out = []
    for i in range(n):
        t = terms[i % len(terms)] if terms else f"parent{i}"
        out.append({"parent": f"{t}-source-{i+1}", "matches": random.randint(3, 42)})
    out.sort(key=lambda x: -x["matches"])
    return out

# --- Real data pilot: Coingecko (public endpoint) ---
def _coingecko_items(terms: List[str]) -> List[Dict]:
    """
    Query Coingecko's simple search and turn results into parent/matches.
    Throttled with in-process TTL cache.
    """
    import httpx

    q = " ".join(sorted(set([t for t in terms if t.strip()]))) or "sol"
    key = ("coingecko", tuple(sorted(set(terms))))  # cache key
    cached = _get_cached(key)
    if cached is not None:
        return cached

    # Simple public search; robust to errors and timeouts
    url = "https://api.coingecko.com/api/v3/search"
    try:
        with httpx.Client(timeout=6.0) as cl:
            r = cl.get(url, params={"query": q})
            r.raise_for_status()
            js = r.json() or {}
    except Exception:
        # network failure → fall back to deterministic
        items = _deterministic_items(q, terms)
        _set_cached(key, items)
        return items

    coins = js.get("coins") or []
    # Build parents with a crude "matches" derived from market cap rank (lower rank → higher score)
    out: List[Dict] = []
    for i, c in enumerate(coins[:8]):  # limit early
        name = c.get("name") or c.get("id") or f"cg-{i}"
        rank = c.get("market_cap_rank") or 1000
        score = max(3, 100 - int(rank))  # bounded 3..97
        out.append({"parent": f"{name}", "matches": score})
    if not out:
        out = _deterministic_items(q, terms)

    out.sort(key=lambda x: -x["matches"])
    # keep top 3 for UI consistency
    out = out[:3]
    _set_cached(key, out)
    return out

class Source:
    def parents_for(self, narrative: str, terms: List[str]) -> List[Dict]:
        if MODE in {"test", "ci"}:
            return _deterministic_items(narrative, terms)
        if MODE == "coingecko":
            return _coingecko_items(terms)
        return _random_items(terms)
