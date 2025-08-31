"""Data source adapters for different providers (test, dev, coingecko)."""

# pylint: disable=too-many-positional-arguments

import os
import time
import typing as t

from .registry import get_adapter_names, make_adapter, register_adapter

# global ttl for raw provider results (seconds)
TTL_SEC = int(os.getenv("SOURCE_TTL", "60"))

# shared raw cache across providers: (provider, normalized_terms) ->
# (ts, items)
_raw_cache: dict[tuple[str, tuple[str, ...]], tuple[float, list[dict]]] = {}
# back-compat alias for older tests/helpers that expect `_cache`
_cache = _raw_cache


def _now() -> float:
    return time.time()


def _normalize_terms(terms: list[str]) -> tuple[str, ...]:
    norm = {t.strip().lower() for t in (terms or []) if t and t.strip()}
    return tuple(sorted(norm))


def _get_raw_cached(
    key: tuple[str, tuple[str, ...]],
) -> t.Optional[list[dict]]:
    hit = _raw_cache.get(key)
    if not hit:
        return None
    ts, val = hit
    if _now() - ts > TTL_SEC:
        return None
    return val


def _set_raw_cached(key: tuple[str, tuple[str, ...]], val: list[dict]) -> None:
    _raw_cache[key] = (_now(), val)


def _memo_raw(
    provider: str,
    terms: list[str],
    producer: t.Callable[[], list[dict]],
) -> list[dict]:
    key = (provider, _normalize_terms(terms))
    cached = _get_raw_cached(key)
    if cached is not None:
        return cached
    val = producer() or []
    _set_raw_cached(key, val)
    return val


# --------------------------
# local item producers (raw)
# --------------------------


def _deterministic_items(narrative: str, terms: list[str]) -> list[dict]:
    # restore: only 3 deterministic rows with matches 11,10,9 (tests
    # expect this)
    base = terms or [narrative, "parent", "seed"]
    return [
        {"parent": f"{base[0]}-source-1", "matches": 11},
        {"parent": f"{base[min(1, len(base)-1)]}-source-2", "matches": 10},
        {"parent": f"{base[min(2, len(base)-1)]}-source-3", "matches": 9},
    ]


def _random_items(terms: list[str]) -> list[dict]:
    # restore: small dev list (tests expect 2..6 items)
    import random

    n = random.randint(2, 6)
    out: list[dict] = []
    for i in range(n):
        t0 = terms[i % len(terms)] if terms else f"parent{i}"
        out.append(
            {"parent": f"{t0}-source-{i+1}", "matches": random.randint(3, 42)},
        )
    out.sort(key=lambda x: -x["matches"])
    return out


# ---------------
# seed semantics
# ---------------


def _apply_seed_semantics(  # pylint: disable=too-many-positional-arguments
    narrative: str,
    terms: list[str],
    allow_name_match: bool,
    block: list[str] | None,
    items: list[dict],
    require_all_terms: bool = False,
    cap: int | None = 3,  # new: optional cap (default 3 for test/dev)
) -> list[dict]:
    nl = (narrative or "").lower()
    term_list = [t.lower() for t in (terms or []) if t]
    block_list = [b.lower() for b in (block or []) if b]

    filtered: list[dict] = []
    for it in items:
        p = str(it.get("parent", "")).lower()
        if any(b in p for b in block_list):
            continue
        if (
            not allow_name_match
            and nl
            and nl in p
            and not any(t_ in p for t_ in term_list if t_ != nl)
        ):
            continue
        if (
            require_all_terms
            and term_list
            and not all(t_ in p for t_ in term_list)
        ):
            continue
        filtered.append(it)

    filtered.sort(key=lambda x: -int(x.get("matches", 0)))
    return filtered if cap is None else filtered[:cap]  # new: conditional trim


# -------------------------
# providers (registered)
# -------------------------


@register_adapter("test")
def _make_test() -> t.Any:
    class _TestAdapter:  # pylint: disable=too-few-public-methods
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=missing-function-docstring
        def parents_for(
            self,
            narrative: str,
            terms: list[str],
            allow_name_match: bool = True,
            block: list[str] | None = None,
            require_all_terms: bool = False,
        ) -> list[dict]:
            raw = _memo_raw(
                "test",
                terms,
                lambda: _deterministic_items(narrative, terms),
            )
            return _apply_seed_semantics(
                narrative,
                terms,
                allow_name_match,
                block or [],
                raw,
                require_all_terms,
                cap=3,
            )

    return _TestAdapter()


@register_adapter("dev")
def _make_dev() -> t.Any:
    class _DevAdapter:  # pylint: disable=too-few-public-methods
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=missing-function-docstring
        def parents_for(
            self,
            narrative: str,
            terms: list[str],
            allow_name_match: bool = True,
            block: list[str] | None = None,
            require_all_terms: bool = False,
        ) -> list[dict]:
            raw = _memo_raw("dev", terms, lambda: _random_items(terms))
            return _apply_seed_semantics(
                narrative,
                terms,
                allow_name_match,
                block or [],
                raw,
                require_all_terms,
                cap=3,
            )

    return _DevAdapter()


@register_adapter("coingecko")
def _make_cg() -> t.Any:
    import httpx

    class _CGAdapter:  # pylint: disable=too-few-public-methods
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=missing-function-docstring
        def parents_for(
            self,
            narrative: str,
            terms: list[str],
            allow_name_match: bool = True,
            block: list[str] | None = None,
            require_all_terms: bool = False,
        ) -> list[dict]:
            def _fetch() -> list[dict]:
                try:
                    q = (
                        " ".join(sorted({t for t in terms if t.strip()}))
                        or "sol"
                    )
                    url = "https://api.coingecko.com/api/v3/search"
                    with httpx.Client(timeout=6.0) as cl:
                        r = cl.get(url, params={"query": q})
                        r.raise_for_status()
                        js = r.json() or {}
                    coins = js.get("coins") or []
                    out: list[dict] = []
                    for i, c in enumerate(
                        coins[:50],
                    ):  # keep many for pagination
                        name = c.get("name") or c.get("id") or f"cg-{i}"
                        rank = c.get("market_cap_rank") or 1000
                        score = max(3, 100 - int(rank))
                        out.append({"parent": name, "matches": score})
                    if not out:
                        out = _deterministic_items(q, terms)
                    out.sort(key=lambda x: -x["matches"])
                    return out  # no local trim
                except Exception:  # pylint: disable=broad-exception-caught
                    q = (
                        " ".join(sorted({t for t in terms if t.strip()}))
                        or "sol"
                    )
                    return _deterministic_items(q, terms)

            raw = _memo_raw("coingecko", terms, _fetch)
            return _apply_seed_semantics(
                narrative,
                terms,
                allow_name_match,
                block or [],
                raw,
                require_all_terms,
                cap=None,  # no cap for cg
            )

    return _CGAdapter()


# ---------------------------------
# public façade (kept for callers)
# ---------------------------------

MODE = (os.getenv("SOURCE_MODE") or "dev").lower()


class Source:
    """Thin façade that delegates to the selected adapter from the registry.

    :param provider: Provider name, defaults to environment setting.
    """

    def __init__(self, provider: str | None = None) -> None:
        self._name = (provider or MODE).lower()
        self._impl = make_adapter(self._name)

    @staticmethod
    def available() -> list[str]:
        """Get list of available adapter names.

        :return: List of available adapter names.
        """
        return get_adapter_names()

    def parents_for(  # pylint: disable=too-many-positional-arguments
        self,
        narrative: str,
        terms: list[str],
        allow_name_match: bool = True,
        block: list[str] | None = None,
        require_all_terms: bool = False,
    ) -> list[dict]:
        """Get parent data for a narrative and terms.

        :param narrative: The narrative to get parent data for.
        :param terms: The terms to get parent data for.
        :param allow_name_match: Whether to allow name match.
        :param block: The block to get parent data for.
        :param require_all_terms: Whether to require all terms.
        :return: Parent data.
        """
        return self._impl.parents_for(
            narrative,
            terms,
            allow_name_match=allow_name_match,
            block=block,
            require_all_terms=require_all_terms,
        )
