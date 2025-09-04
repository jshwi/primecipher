"""DexScreener adapter for fetching parent data."""

import time
from typing import Any

import httpx

from . import AdapterProtocol


class DexScreenerAdapter(
    AdapterProtocol,
):  # pylint: disable=too-few-public-methods
    """Adapter for DexScreener data source."""

    def fetch_parents(
        self,
        narrative: str,
        terms: list[str],
    ) -> list[dict]:  # pragma: no cover
        """Fetch parent data from DexScreener.

        Queries DexScreener API for each term, merges results, and returns
        normalized parent data.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: List of parent dictionaries with normalized scores.
        """
        if not terms:
            return []

        # Cap to first 3 terms
        capped_terms = terms[:3]
        all_pairs = []

        # Query each term with rate limiting
        for i, term in enumerate(capped_terms):
            if i > 0:  # Sleep between queries (except first)
                time.sleep(0.2)  # 200ms rate limit

            pairs = self._query_dexscreener(term)
            all_pairs.extend(pairs)

        # Deduplicate by token address/symbol
        unique_parents = self._deduplicate_pairs(all_pairs)

        # Normalize scores and return top 25
        return self._normalize_and_rank(unique_parents)

    def _query_dexscreener(self, query: str) -> list[dict[str, Any]]:
        """Query DexScreener API for a single term.

        :param query: Search query term.
        :return: List of pair data from API response.
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    "https://api.dexscreener.com/latest/dex/search",
                    params={"q": query},
                )
                response.raise_for_status()
                data = response.json()

                # Extract pairs from response
                pairs = data.get("pairs", [])
                return pairs if isinstance(pairs, list) else []

        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
            KeyError,
            ValueError,
        ):
            # Return empty list on any API error
            return []

    def _deduplicate_pairs(
        self,
        pairs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Deduplicate pairs by token address and symbol.

        :param pairs: List of pair data from API.
        :return: Deduplicated list of pairs.
        """
        seen = set()
        unique_pairs = []

        for pair in pairs:
            # Get base token info
            base_token = pair.get("baseToken", {})
            token_address = base_token.get("address", "")
            symbol = base_token.get("symbol", "")

            # Create dedup key
            key = (token_address.lower(), symbol.lower())
            if key not in seen and token_address and symbol:
                seen.add(key)
                unique_pairs.append(pair)

        return unique_pairs

    def _normalize_and_rank(self, pairs: list[dict[str, Any]]) -> list[dict]:
        """Normalize scores and return top 25 parents.

        :param pairs: List of deduplicated pairs.
        :return: List of parent dictionaries with normalized scores.
        """
        if not pairs:
            return []

        # Extract volumes for normalization
        max_volume = self._get_max_volume(pairs)

        # Build parent dictionaries
        parents = [self._build_parent_dict(pair, max_volume) for pair in pairs]

        # Sort by score (descending) and return top 25
        parents.sort(key=lambda x: x["score"], reverse=True)
        return parents[:25]

    def _get_max_volume(self, pairs: list[dict[str, Any]]) -> float:
        """Get maximum 24h volume from pairs.

        :param pairs: List of pair data.
        :return: Maximum volume value.
        """
        volumes = []
        for pair in pairs:
            volume_data = pair.get("volume", {})
            vol_24h = volume_data.get("h24", 0) or 0
            volumes.append(vol_24h)
        return max(volumes) if volumes else 0

    def _build_parent_dict(
        self,
        pair: dict[str, Any],
        max_volume: float,
    ) -> dict:
        """Build parent dictionary from pair data.

        :param pair: Pair data from API.
        :param max_volume: Maximum volume for score normalization.
        :return: Parent dictionary.
        """
        base_token = pair.get("baseToken", {})
        volume_data = pair.get("volume", {})
        vol_24h = volume_data.get("h24", 0) or 0

        # Calculate normalized score
        score = vol_24h / max_volume if max_volume > 0 else 0.0

        # Get token info with defaults
        token_name = base_token.get("name", "")
        symbol = base_token.get("symbol", "")
        token_address = base_token.get("address", "")

        # Use token name or symbol as display name
        display_name = token_name or symbol

        # Get pair URL and chain info
        pair_url = pair.get("pairUrl", "")
        chain_id = pair.get("chainId", "")

        # Build children (evidence/pairs)
        children = self._build_children(pair, vol_24h)

        return {
            "name": display_name,
            "symbol": symbol,
            "score": score,
            "source": "dexscreener",
            "url": pair_url,
            "chain": chain_id,
            "address": token_address,
            "children": children,
        }

    def _build_children(
        self,
        pair: dict[str, Any],
        vol_24h: float,
    ) -> list[dict]:
        """Build children list from pair data.

        :param pair: Pair data from API.
        :param vol_24h: 24h volume for this pair.
        :return: List of child dictionaries.
        """
        pair_url = pair.get("pairUrl", "")
        chain_id = pair.get("chainId", "")

        if not pair_url or not chain_id:
            return []

        return [
            {
                "pair": pair.get("pairAddress", ""),
                "chain": chain_id,
                "dex": pair.get("dexId", ""),
                "url": pair_url,
                "vol24h": vol_24h,
            },
        ]
