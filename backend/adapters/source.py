"""Data source adapters for different providers (test, dev, coingecko)."""

# pylint: disable=too-many-positional-arguments

import logging
import os
import random
import time
import typing as t

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .registry import get_adapter_names, make_adapter, register_adapter

# global ttl for raw provider results (seconds)
TTL_SEC = int(os.getenv("SOURCE_TTL", "60"))

# Rate limiting configuration
CG_RPS = float(os.getenv("CG_RPS", "0.5"))  # max requests per second
CG_BURST = int(os.getenv("CG_BURST", "1"))  # allow short bursts
CG_JITTER_MS = int(os.getenv("CG_JITTER_MS", "250"))  # jitter in milliseconds

# shared raw cache across providers: (provider, normalized_terms) ->
# (ts, items)
_raw_cache: dict[tuple[str, tuple[str, ...]], tuple[float, list[dict]]] = {}
# back-compat alias for older tests/helpers that expect `_cache`
_cache = _raw_cache

# search cache for individual terms: term_lower -> (ts, coin_ids)
_search_cache: dict[str, tuple[float, list[str]]] = {}

# Module-level logger
logger = logging.getLogger(__name__)

# Module-level counter for CG API calls
_CG_CALLS_COUNT = 0


def get_cg_calls_count() -> int:
    """Get the current number of CG API calls made.

    :return: Current call count.
    """
    return _CG_CALLS_COUNT


def reset_cg_calls_count() -> None:
    """Reset the CG API calls counter to zero."""
    global _CG_CALLS_COUNT  # pylint: disable=global-statement
    _CG_CALLS_COUNT = 0


class TokenBucket:  # pylint: disable=too-few-public-methods
    """Simple token bucket rate limiter for CoinGecko requests.

    :param rps: Requests per second (tokens per second).
    :param burst: Maximum burst capacity.
    """

    def __init__(self, rps: float, burst: int) -> None:
        """Initialize token bucket."""
        self.rps = rps
        self.capacity = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def acquire(self) -> None:
        """Acquire a token, blocking if necessary."""
        now = time.monotonic()
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rps)
        self.last_refill = now

        # If no tokens available, wait
        if self.tokens < 1.0:
            wait_time = (1.0 - self.tokens) / self.rps
            time.sleep(wait_time)
            # Update tokens after waiting
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rps)
            self.last_refill = now

        # Consume one token
        self.tokens -= 1.0


# Module-level rate limiter for CoinGecko
_cg_limiter = TokenBucket(CG_RPS, CG_BURST)

# Module-level Session for CoinGecko calls
sess = requests.Session()
sess.headers.update(
    {
        "accept": "application/json",
        "user-agent": "primecipher/0.0.0 (+https://primecipher.local)",
    },
)
adapter = HTTPAdapter(
    max_retries=Retry(
        total=3,
        connect=2,
        read=2,
        status=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        raise_on_status=False,
        respect_retry_after_header=True,
    ),
)
sess.mount("https://", adapter)


def _get_json(
    url: str,
    params: dict[str, t.Any] | None = None,
) -> t.Optional[t.Union[dict, list]]:
    """Get JSON data from URL with exponential backoff retry logic.

    Args:
        url: URL to fetch
        params: Query parameters

    Returns:
        JSON data or None on error
    """
    # Backoff configuration
    base_delay = 0.8  # base delay in seconds
    max_backoff = 30.0  # maximum backoff in seconds
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            # Rate limit: acquire token before making request
            _cg_limiter.acquire()

            # Increment CG calls counter
            global _CG_CALLS_COUNT  # pylint: disable=global-statement
            _CG_CALLS_COUNT += 1

            # Add small random jitter after acquiring token
            jitter_ms = random.randint(0, CG_JITTER_MS)
            time.sleep(jitter_ms / 1000.0)

            r = sess.get(url, params=params, timeout=10)

            # Handle 429 (rate limited) with Retry-After header
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    sleep_time = int(retry_after)
                    logger.debug(
                        "[CG] 429 rate limited, sleeping %ds (Retry-After)",
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                else:
                    # Calculate exponential backoff with jitter
                    jitter = random.uniform(0, 0.3)
                    backoff_delay = min(
                        base_delay * (2**attempt) + jitter,
                        max_backoff,
                    )
                    logger.debug(
                        "[CG] 429 rate limited, sleeping %.2fs (backoff)",
                        backoff_delay,
                    )
                    time.sleep(backoff_delay)

                # Continue to next attempt
                continue

            # Handle 5xx server errors with exponential backoff
            if 500 <= r.status_code < 600 and attempt < max_attempts - 1:
                # Don't sleep on last attempt
                jitter = random.uniform(0, 0.3)
                backoff_delay = min(
                    base_delay * (2**attempt) + jitter,
                    max_backoff,
                )
                logger.debug(
                    "[CG] %d server error, sleeping %.2fs (backoff)",
                    r.status_code,
                    backoff_delay,
                )
                time.sleep(backoff_delay)
                continue

            # For successful responses or non-retryable errors, raise
            r.raise_for_status()
            return r.json()

        except (requests.RequestException, ValueError, KeyError) as e:
            # Log debug for individual attempt failures
            logger.debug(
                "[CG] attempt %d/%d failed: %s",
                attempt + 1,
                max_attempts,
                e,
            )

            # If this was the last attempt, log warning and return None
            if attempt == max_attempts - 1:
                logger.warning(
                    "[CG] all %d attempts failed for url=%s params=%s",
                    max_attempts,
                    url,
                    params,
                )
                return None

            # Calculate backoff for next attempt
            jitter = random.uniform(0, 0.3)
            backoff_delay = min(
                base_delay * (2**attempt) + jitter,
                max_backoff,
            )
            logger.debug(
                "[CG] sleeping %.2fs before retry %d/%d",
                backoff_delay,
                attempt + 2,
                max_attempts,
            )
            time.sleep(backoff_delay)

    return None


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


def _get_search_cached(term: str) -> t.Optional[list[str]]:
    """Get cached search results for a term.

    :param term: Search term (will be lowercased).
    :return: Cached coin IDs or None if not found/expired.
    """
    term_lower = term.strip().lower()
    hit = _search_cache.get(term_lower)
    if not hit:
        return None
    ts, coin_ids = hit
    # TTL = 15 minutes = 900 seconds
    if _now() - ts > 900:
        return None
    return coin_ids


def _set_search_cached(term: str, coin_ids: list[str]) -> None:
    """Cache search results for a term.

    :param term: Search term (will be lowercased).
    :param coin_ids: List of coin IDs to cache.
    """
    term_lower = term.strip().lower()
    _search_cache[term_lower] = (_now(), coin_ids)


def clear_search_cache() -> None:
    """Clear the search cache. Used for testing."""
    _search_cache.clear()


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
    class _CGAdapter:  # pylint: disable=too-few-public-methods
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=missing-function-docstring

        def _filter_terms(self, terms: list[str]) -> list[str]:
            """Filter terms: take first 2, skip generic/short ones.

            :param terms: List of search terms.
            :return: Filtered list of terms.
            """
            if not terms:
                return []

            # Skip very generic/short terms
            generic_terms = {"swap", "defi", "nft", "play", "fun", "meta"}
            filtered = []

            for term in terms[:2]:  # Take first 2 only
                if (
                    term
                    and term.strip()
                    and len(term.strip()) >= 3
                    and term.strip().lower() not in generic_terms
                ):
                    filtered.append(term.strip())

            return filtered

        def _search_coins(self, terms: list[str]) -> list[str]:
            """Search for coins using terms and collect coin IDs.

            :param terms: List of search terms.
            :return: List of unique coin IDs.
            """
            coin_ids = set()
            failed_terms = []
            http_calls_made = 0

            for term in terms:
                try:
                    # Check cache first
                    cached_ids = _get_search_cached(term)
                    if cached_ids is not None:
                        logger.debug("[CG] cache hit for term: %s", term)
                        coin_ids.update(cached_ids)
                        continue

                    # Sleep ≥ 1.2s between /search calls
                    # (in addition to token-bucket)
                    if http_calls_made > 0:
                        time.sleep(1.2)

                    url = "https://api.coingecko.com/api/v3/search"
                    params = {"query": term.strip()}

                    data = _get_json(url, params) or {}
                    if isinstance(data, dict):
                        coins = data.get("coins", [])
                    else:
                        coins = []

                    # Collect at most 5 ids per term
                    term_coin_ids = []
                    for coin in coins[:5]:
                        coin_id = coin.get("id")
                        if coin_id:
                            coin_ids.add(coin_id)
                            term_coin_ids.append(coin_id)

                    # Cache the results for this term
                    if term_coin_ids:
                        _set_search_cached(term, term_coin_ids)
                        logger.debug(
                            "[CG] cached %d ids for term: %s",
                            len(term_coin_ids),
                            term,
                        )

                    http_calls_made += 1

                except Exception:  # pylint: disable=broad-exception-caught
                    # Track failed terms for logging
                    failed_terms.append(term)
                    continue

            # Log warning if all terms failed
            if failed_terms and len(failed_terms) == len(terms):
                logger.warning(
                    "[CG] search failed for all %d terms: %s",
                    len(terms),
                    failed_terms,
                )

            return list(coin_ids)

        def _get_market_data(self, coin_ids: list[str]) -> list[dict]:
            """Get detailed market data for coin IDs in batches.

            :param coin_ids: List of coin IDs to fetch data for.
            :return: List of market data dictionaries.
            """
            if not coin_ids:
                return []

            all_market_data = []

            # Batch ids into chunks of ≤10
            batch_size = 10
            for i in range(0, len(coin_ids), batch_size):
                batch = coin_ids[slice(i, i + batch_size)]
                try:
                    url = "https://api.coingecko.com/api/v3/coins/markets"
                    params = {
                        "vs_currency": "usd",
                        "ids": ",".join(batch),
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": 1,
                        "sparkline": "false",
                    }

                    data = _get_json(url, params) or []
                    rows = data if isinstance(data, list) else []

                    if rows:  # If we got data, add it
                        all_market_data.extend(rows)
                        # Stop after first non-empty batch
                        break

                except Exception:  # pylint: disable=broad-exception-caught
                    logger.debug(
                        "[CG] market data fetch failed for batch %d/%d",
                        i // batch_size + 1,
                        (len(coin_ids) + batch_size - 1) // batch_size,
                    )
                    continue

                # Sleep ≥ 1.5s between batches (except for the last batch)
                if i + batch_size < len(coin_ids):
                    time.sleep(1.5)

            return all_market_data

        def _map_market_to_items(self, market_data: list[dict]) -> list[dict]:
            """Map CoinGecko market rows to parent dicts with scoring.

            :param market_data: List of market data from CoinGecko API.
            :return: List of formatted parent dictionaries.
            """
            if not market_data:
                return []

            items = []
            for row in market_data:
                # Extract fields as specified
                name = (row.get("name") or "").strip()
                if not name:
                    continue

                symbol = (row.get("symbol") or "").upper()
                price = float(row.get("current_price") or 0)
                market_cap = float(row.get("market_cap") or 0)
                vol24h = float(row.get("total_volume") or 0)
                image = row.get("image")
                url = f"https://www.coingecko.com/en/coins/{row.get('id', '')}"

                item = {
                    "parent": name,
                    "matches": 0,  # set below
                    "symbol": symbol or None,
                    "price": price if price else None,
                    "marketCap": market_cap if market_cap else None,
                    "vol24h": vol24h if vol24h else None,
                    "image": image,
                    "url": url,
                    "source": "coingecko",
                }
                items.append(item)

            # Apply volume-based scoring
            vols = [float(it["vol24h"] or 0) for it in items]
            if any(v > 0 for v in vols):
                max_v = max(vols)
                for it in items:
                    vol = float(it["vol24h"] or 0)
                    it["matches"] = int(round(100 * (vol / max_v)))
            else:
                for it in items:
                    it["matches"] = 10

            # Sort by matches desc, then marketCap desc, then parent asc
            items.sort(
                key=lambda x: (
                    -int(x["matches"] or 0),
                    -float(x["marketCap"] or 0),
                    x["parent"],
                ),
            )

            # Cap: keep top 25 by matches after mapping
            return items[:25]

        def parents_for(
            self,
            narrative: str,
            terms: list[str],
            allow_name_match: bool = True,
            block: list[str] | None = None,
            require_all_terms: bool = False,
        ) -> list[dict]:
            def _fetch() -> list[dict]:
                # Filter terms: take first 3, skip generic/short ones
                search_terms = self._filter_terms(terms)
                if not search_terms:
                    logger.debug(
                        "[CG] %s: no valid search terms after filtering",
                        narrative,
                    )
                    return []

                # Collect coin IDs from search API
                coin_ids = self._search_coins(search_terms)
                if not coin_ids:
                    logger.warning(
                        "[CG] %s: no coin IDs found for terms: %s",
                        narrative,
                        search_terms,
                    )
                    return []

                # Fetch market data for the coin IDs
                market_data = self._get_market_data(coin_ids)

                # Map market data to parent dicts with scoring
                items = self._map_market_to_items(market_data)

                # Log once per narrative
                logger.info(
                    "[CG] %s ids=%d markets=%d mapped=%d",
                    narrative,
                    len(coin_ids),
                    len(market_data),
                    len(items),
                )

                return items

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
            return parents

        def fetch_parents(
            self,
            narrative: str,
            terms: list[str],
        ) -> list[dict]:
            """Fetch parent data for a narrative and terms.

            :param narrative: The narrative to get parent data for.
            :param terms: The terms to get parent data for.
            :return: Parent data.
            """
            return self.parents_for(narrative, terms)

    return _CGAdapter()


def parents_for_dexscreener(  # pylint: disable=too-many-branches
    narrative: str,
    terms: list[str],
) -> list[dict]:
    """Get parent data from Dexscreener API for given terms.

    :param narrative: The narrative name (for logging).
    :param terms: List of search terms.
    :return: List of parent items with dexscreener data.
    """
    # Keep only first 3 terms; skip terms with len<3 or generic ones
    generic_terms = {"swap", "defi", "nft", "play", "fun", "meta"}
    filtered_terms = []

    for term in terms[:3]:  # Take first 3 only
        if (
            term
            and term.strip()
            and len(term.strip()) >= 3
            and term.strip().lower() not in generic_terms
        ):
            filtered_terms.append(term.strip())

    if not filtered_terms:
        logger.info("[DS] %s terms=0 parents=0", narrative)
        return []

    # Collect all results with deduplication by (chain, lowercase(address))
    results_by_key: dict[tuple[str, str], dict] = {}

    for term in filtered_terms:
        try:
            url = "https://api.dexscreener.com/latest/dex/search"
            params = {"q": term}

            data = _get_json(url, params)
            if not data or not isinstance(data, dict):
                continue

            pairs = data.get("pairs", [])
            if not pairs:
                continue

            for pair in pairs:
                # Extract base token data
                base_token = pair.get("baseToken", {})
                if not base_token:
                    continue

                # Get required fields
                name = base_token.get("name") or base_token.get("symbol")
                symbol = base_token.get("symbol")
                chain = pair.get("chainId")
                address = base_token.get("address") or pair.get("pairAddress")

                if not name or not chain or not address:
                    continue

                # Get optional numeric fields
                price = None
                try:
                    price_usd = pair.get("priceUsd")
                    if price_usd:
                        price = float(price_usd)
                except (ValueError, TypeError):
                    pass

                vol24h = None
                try:
                    # Try volume.h24 first, then volume24h
                    volume = pair.get("volume", {})
                    if isinstance(volume, dict) and "h24" in volume:
                        vol24h = float(volume["h24"])
                    elif "volume24h" in pair:
                        vol24h = float(pair["volume24h"])
                except (ValueError, TypeError):
                    pass

                fdv = None
                try:
                    fdv_val = pair.get("fdv")
                    if fdv_val:
                        fdv = float(fdv_val)
                except (ValueError, TypeError):
                    pass

                liq = None
                try:
                    liquidity = pair.get("liquidity", {})
                    if isinstance(liquidity, dict) and "usd" in liquidity:
                        liq = float(liquidity["usd"])
                except (ValueError, TypeError):
                    pass

                url_val = pair.get("url") or pair.get("pairUrl")

                # Create deduplication key
                key = (chain, address.lower())

                # Check if we should keep this result (higher vol24h wins)
                existing = results_by_key.get(key)
                if existing:
                    existing_vol = existing.get("vol24h") or 0
                    current_vol = vol24h or 0
                    if current_vol <= existing_vol:
                        continue

                # Store result
                results_by_key[key] = {
                    "parent": name,
                    "matches": 0,  # set below
                    "symbol": symbol or None,
                    "price": price,
                    "vol24h": vol24h,
                    "marketCap": fdv,  # fdv as a cap proxy
                    "liquidityUsd": liq,
                    "chain": chain,
                    "address": address,
                    "url": url_val,
                    "source": "dexscreener",
                }

        except Exception:  # pylint: disable=broad-exception-caught
            # Continue with next term on any error
            continue

        # Short sleep between calls (≥ 300ms)
        time.sleep(0.3)

    items = list(results_by_key.values())

    # Apply scoring
    vols = [it["vol24h"] or 0 for it in items]
    if any(v > 0 for v in vols):
        max_v = max(vols)
        for it in items:
            it["matches"] = int(round(100 * ((it["vol24h"] or 0) / max_v)))
    elif any((it.get("liquidityUsd") or 0) > 0 for it in items):
        liquidity_vals = [it["liquidityUsd"] or 0 for it in items]
        max_l = max(liquidity_vals)
        for it in items:
            it["matches"] = int(
                round(100 * ((it["liquidityUsd"] or 0) / max_l)),
            )
    else:
        for it in items:
            it["matches"] = 10

    # Sort by matches desc, vol24h desc, liquidityUsd desc, parent asc
    items.sort(
        key=lambda x: (
            -int(x["matches"] or 0),
            -float(x["vol24h"] or 0),
            -float(x["liquidityUsd"] or 0),
            x["parent"],
        ),
    )

    # Cap to 25
    items = items[:25]

    logger.info(
        "[DS] %s terms=%d parents=%d",
        narrative,
        len(filtered_terms),
        len(items),
    )
    return items


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
