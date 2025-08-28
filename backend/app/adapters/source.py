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
    out: List[Dict] = []
    for i in range(n):
        t = terms[i % len(terms)] if terms else f"parent{i}"
        out.append({"parent": f"{t}-source-{i+1}", "matches": random.randint(3, 42)})
    out.sort(key=lambda x: -x["matches"])
    return out

def _coingecko_items(terms: List[str]) -> List[Dict]:
    import httpx
    q = " ".join(sorted(set([t for t in terms if t.strip()]))) or "sol"
    key = ("coingecko", tuple(sorted(set(terms))))
    cached = _get_cached(key)
    if cached is not None:
        return cached
    url = "https://api.coingecko.com/api/v3/search"
    try:
        with httpx.Client(timeout=6.0) as cl:
            r = cl.get(url, params={"query": q})
            r.raise_for_status()
            js = r.json() or {}
    except Exception:
        items = _deterministic_items(q, terms)
        _set_cached(key, items)
        return items

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
    out = out[:3]
    _set_cached(key, out)
    return out

# ---------- NEW: seed semantics ----------
def _apply_seed_semantics(
    narrative: str,
    terms: List[str],
    allow_name_match: bool,
    block: List[str] | None,
    items: List[Dict],
    require_all_terms: bool = False,   # <-- add this
) -> List[Dict]:
    nl = narrative.lower()
    term_list = [t.lower() for t in (terms or []) if t]
    block_list = [b.lower() for b in (block or []) if b]

    filtered: List[Dict] = []
    for it in items:
        p = str(it.get("parent", "")).lower()
        # blocklist
        if any(b in p for b in block_list):
            continue
        # allowNameMatch
        if not allow_name_match and nl and nl in p:
            if not any(t in p for t in term_list if t != nl):
                continue
        # requireAllTerms
        if require_all_terms and term_list:
            if not all(t in p for t in term_list):
                continue
        filtered.append(it)

    filtered.sort(key=lambda x: -int(x.get("matches", 0)))
    return filtered[:3]

class Source:
    def parents_for(
        self,
        narrative: str,
        terms: List[str],
        allow_name_match: bool = True,
        block: List[str] | None = None,
        require_all_terms: bool = False,  # ignored in commit 1; wired in commit 2
    ) -> List[Dict]:
        if MODE in {"test", "ci"}:
            raw = _deterministic_items(narrative, terms)
        elif MODE == "coingecko":
            raw = _coingecko_items(terms)
        else:
            raw = _random_items(terms)
        return _apply_seed_semantics(narrative, terms, allow_name_match, block, raw)
