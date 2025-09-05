"""Data source adapters for different providers (test, dev, coingecko)."""

# pylint: disable=too-many-positional-arguments

import logging
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

        def _search_coins(
            self,
            terms: list[str],
        ) -> tuple[list[str], list[dict]]:
            """Search for coins using terms and collect IDs and results.

            For the first 3 seed terms:
            - GET https://api.coingecko.com/api/v3/search?query={term}
            - Collect up to 10 ids from .coins[].id
            - Sleep ~250ms between terms
            - Merge and dedupe ids; cap total to 30
            - If no ids → return [] immediately
            """
            coin_ids: set[str] = set()
            search_results: list[dict] = []

            # Use only first 3 seed terms
            search_terms = (terms or [])[:3]
            if not search_terms:
                logging.info("[CG] no search terms provided")
                return [], []

            for term in search_terms:
                if not term or not term.strip():
                    continue

                try:
                    # Rate limit: sleep ~250ms between requests
                    time.sleep(0.25)

                    url = "https://api.coingecko.com/api/v3/search"
                    params = {"query": term.strip()}

                    with httpx.Client(timeout=10.0) as client:
                        response = client.get(url, params=params)
                        response.raise_for_status()
                        data = response.json() or {}

                    coins = data.get("coins", [])
                    # Collect up to 10 ids per term and add to search results
                    term_ids = self._process_search_coins(
                        coins,
                        coin_ids,
                        search_results,
                    )

                    # Log search results for this term
                    logging.info("[CG] term=%s ids=%d", term, len(term_ids))

                except Exception:  # pylint: disable=broad-exception-caught
                    # Continue with other terms if one fails
                    logging.warning("[CG] failed to search term=%s", term)
                    continue

            # Merge and dedupe ids; cap total to 30
            final_ids = list(coin_ids)[:30]
            logging.info("[CG] final id count=%d", len(final_ids))

            return final_ids, search_results[:50]

        def _process_search_coins(
            self,
            coins: list[dict],
            coin_ids: set[str],
            search_results: list[dict],
        ) -> list[str]:
            """Process search results and collect coin IDs.

            Args:
                coins: List of coin data from search API
                coin_ids: Set to add collected IDs to
                search_results: List to add all coins to

            Returns:
                List of IDs collected from this batch
            """
            term_ids = []
            for coin in coins[:10]:
                coin_id = coin.get("id")
                if coin_id:
                    coin_ids.add(coin_id)
                    term_ids.append(coin_id)
                # Always add to search results for fallback
                search_results.append(coin)
            return term_ids

        def _get_market_data(self, coin_ids: list[str]) -> list[dict]:
            """Get detailed market data for coin IDs."""
            if not coin_ids:
                return []

            try:
                # Rate limit: sleep ~250ms before request
                time.sleep(0.25)

                url = "https://api.coingecko.com/api/v3/coins/markets"
                params = {
                    "vs_currency": "usd",
                    "ids": ",".join(coin_ids),
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": 1,
                    "sparkline": "false",
                }

                with httpx.Client(timeout=10.0) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json() or []

                rows = data if isinstance(data, list) else []
                # Log market data results
                logging.info("[CG] markets rows=%d", len(rows))
                return rows

            except Exception:  # pylint: disable=broad-exception-caught
                return []

        def _filter_valid_parents(self, parents: list[dict]) -> list[dict]:
            """Filter out invalid parent entries."""
            filtered_parents = []
            for parent in parents:
                parent_name = str(parent.get("parent", "")).strip()
                vol24h = float(parent.get("vol24h", 0) or 0)
                market_cap = float(parent.get("marketCap", 0) or 0)

                # Keep if has parent name OR has market value
                if (
                    parent_name
                    and parent_name != "unknown"
                    or (vol24h + market_cap) > 0
                ):
                    filtered_parents.append(parent)
            return filtered_parents

        def _calculate_fallback_matches(
            self,
            parents: list[dict],
            market_data: list[dict],
        ) -> None:
            """Calculate fallback matches using market cap rank."""
            for item in parents:
                market_cap_rank = self._find_market_cap_rank(item, market_data)
                if (
                    market_cap_rank
                    and isinstance(market_cap_rank, (int, float))
                    and market_cap_rank > 0
                ):
                    # Use inverse rank for scoring (lower rank = higher score)
                    item["matches"] = max(1, int(round(100 / market_cap_rank)))
                else:
                    # Minimal nonzero fallback to avoid all-zero UI
                    item["matches"] = 10

        def _find_market_cap_rank(
            self,
            item: dict,
            market_data: list[dict],
        ) -> t.Optional[t.Union[int, float]]:
            """Find market cap rank for an item from market data."""
            item_url = item.get("url", "")
            item_name = item.get("parent", "")
            if not item_url or not item_name:
                return None

            coin_id = item_url.split("/")[-1] if "/" in item_url else ""
            for market_row in market_data:
                if (
                    market_row.get("id") == coin_id
                    or market_row.get("name") == item_name
                ):
                    return market_row.get("market_cap_rank")
            return None

        def _map_market_to_parents(
            self,
            market_data: list[dict],
        ) -> list[dict]:
            """Map CoinGecko market rows to parent dicts with real values.

            Maps each market row M to parent dict with specified field mapping.
            """
            # Build parents list with exact field mapping as specified
            parents = [
                {
                    "parent": row.get("name")
                    or row.get("symbol")
                    or "unknown",
                    "matches": 0,  # Will be calculated below
                    "vol24h": row.get("total_volume") or 0.0,
                    "marketCap": row.get("market_cap") or 0.0,
                    "price": row.get("current_price") or 0.0,
                    "symbol": row.get("symbol", ""),
                    "image": row.get("image", ""),
                    "url": (
                        f"https://www.coingecko.com/en/coins/"
                        f"{row.get('id', '')}"
                    ),
                    "source": "coingecko",
                }
                for row in market_data
            ]

            # Filter out invalid parent entries
            filtered_parents = self._filter_valid_parents(parents)

            # Compute matches using volume-based scoring
            vols = [
                p["vol24h"]
                for p in filtered_parents
                if isinstance(p["vol24h"], (int, float))
            ]
            max_v = max(vols) if vols else 0

            if max_v > 0:
                for p in filtered_parents:
                    p["matches"] = int(round(100 * (p["vol24h"] / max_v)))
            else:
                # If no volume data, use fallback
                self._calculate_fallback_matches(filtered_parents, market_data)

            # Sort by matches desc; cap to top 25
            filtered_parents.sort(key=lambda x: -x["matches"])
            return filtered_parents[:25]

        def _map_market_to_raw_rows(
            self,
            market_data: list[dict],
        ) -> list[dict]:
            """Map CoinGecko market rows into raw market data rows.

            Returns only the specified fields: name, symbol, image,
            current_price, market_cap, total_volume, id
            """
            raw_rows = []
            for market_row in market_data:
                raw_row = {
                    "name": market_row.get("name", ""),
                    "symbol": market_row.get("symbol", ""),
                    "image": market_row.get("image", ""),
                    "current_price": market_row.get("current_price", 0) or 0,
                    "market_cap": market_row.get("market_cap", 0) or 0,
                    "total_volume": market_row.get("total_volume", 0) or 0,
                    "id": market_row.get("id", ""),
                }
                raw_rows.append(raw_row)

            return raw_rows

        def _map_search_to_parents(
            self,
            search_results: list[dict],
        ) -> list[dict]:
            """Map CoinGecko search results into parent dicts."""
            parents = []
            for i, search_result in enumerate(search_results):
                name = (
                    search_result.get("name")
                    or search_result.get("id")
                    or f"cg-{i}"
                )
                rank = search_result.get("market_cap_rank") or 1000
                score = max(3, 100 - int(rank))
                parent = {
                    "parent": name,
                    "matches": score,
                    "symbol": search_result.get("symbol", ""),
                    "price": 0,  # Not available in search results
                    "marketCap": 0,  # Not available in search results
                    "vol24h": 0,  # Not available in search results
                    "image": search_result.get("large", ""),
                    "url": (
                        f"https://www.coingecko.com/en/coins/"
                        f"{search_result.get('id', '')}"
                    ),
                    "source": "coingecko",
                }
                parents.append(parent)

            # Sort by matches descending
            parents.sort(key=lambda x: -int(x["matches"]))
            return parents

        def parents_for(
            self,
            narrative: str,
            terms: list[str],
            allow_name_match: bool = True,
            block: list[str] | None = None,
            require_all_terms: bool = False,
        ) -> list[dict]:
            def _fetch() -> list[dict]:
                # Use up to first 3 seed terms per narrative
                search_terms = (terms or [])[:3]
                if not search_terms:
                    return []

                # Collect coin IDs and search results from search API
                coin_ids, search_results = self._search_coins(search_terms)
                if not coin_ids and not search_results:
                    # Fallback to deterministic items when no search results
                    q = (
                        " ".join(sorted({t for t in terms if t.strip()}))
                        or "sol"
                    )
                    return _deterministic_items(q, terms)

                # Try to fetch market data for the coin IDs
                market_data = (
                    self._get_market_data(coin_ids) if coin_ids else []
                )

                if market_data:
                    # Use market data if available (preferred approach)
                    # Return parent dicts with metadata as requested
                    return self._map_market_to_parents(market_data)
                if search_results:
                    # Fall back to search results if no market data
                    return self._map_search_to_parents(search_results)

                # This should never be reached in normal circumstances
                # as search_results will always be processed above
                raise RuntimeError(  # pragma: no cover
                    "Unexpected code path: no market data and no search"
                    " results",
                )

            raw = _memo_raw("coingecko", terms, _fetch)
            parents = _apply_seed_semantics(
                narrative,
                terms,
                allow_name_match,
                block or [],
                raw,
                require_all_terms,
                cap=None,  # no cap for cg
            )
            # Log final mapped parents count
            logging.info(
                "[CG] mapped=%d first=%s",
                len(parents),
                (parents[0].get("symbol") if parents else "-"),
            )
            return parents

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
