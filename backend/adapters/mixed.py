"""Mixed adapter that merges DexScreener and CoinGecko data."""

import logging
from dataclasses import dataclass

from . import AdapterProtocol
from .coingecko import CoinGeckoAdapter
from .dexscreener import DexScreenerAdapter

logger = logging.getLogger(__name__)


@dataclass
class ContributionCounts:
    """Data class for contribution counts logging."""

    narrative: str
    terms: list[str]
    cg_data: list[dict]
    ds_data: list[dict]
    merged_items: list[dict]


class MixedAdapter(AdapterProtocol):  # pylint: disable=too-few-public-methods
    """Adapter that merges DexScreener and CoinGecko data sources."""

    def __init__(self):
        """Initialize the mixed adapter with both source adapters."""
        self.cg_adapter = CoinGeckoAdapter()
        self.ds_adapter = DexScreenerAdapter()

    def fetch_parents(self, narrative: str, terms: list[str]) -> list[dict]:
        """Fetch and merge parent data from both DexScreener and CoinGecko.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: List of merged parent dictionaries with normalized scores.
        """
        if not terms:
            return []

        # Fetch data from both sources with error handling
        cg_data = []
        ds_data = []
        cg_error = None
        ds_error = None

        try:
            cg_data = self.cg_adapter.fetch_parents(narrative, terms)
        except Exception as e:  # pylint: disable=broad-exception-caught
            cg_error = str(e)
            logger.warning("[MIXED] %s CG failed: %s", narrative, cg_error)

        try:
            ds_data = self.ds_adapter.fetch_parents(narrative, terms)
        except Exception as e:  # pylint: disable=broad-exception-caught
            ds_error = str(e)
            logger.warning("[MIXED] %s DS failed: %s", narrative, ds_error)

        # Merge the data according to the specified rules
        merged_data = self._merge_data(cg_data, ds_data, narrative, terms)

        # Re-normalize scores within the merged set
        return self._renormalize_scores(merged_data)

    def _merge_data(  # pylint: disable=too-many-locals,too-many-branches
        # pylint: disable=too-many-statements
        self,
        cg_data: list[dict],
        ds_data: list[dict],
        narrative: str,
        terms: list[str],
    ) -> list[dict]:
        """Merge CoinGecko and DexScreener data by symbol/address.

        :param cg_data: CoinGecko parent data.
        :param ds_data: DexScreener parent data.
        :param narrative: The narrative name for logging.
        :param terms: List of search terms for logging.
        :return: Merged parent data.
        """
        # Create lookup dictionaries indexed by stable unique keys
        cg_by_key = {}
        ds_by_key = {}

        # Index CoinGecko data with stable unique keys
        for item in cg_data:
            key = self._get_stable_key(item)
            if key:
                cg_by_key[key] = item

        # Index DexScreener data with stable unique keys
        for item in ds_data:
            key = self._get_stable_key(item)
            if key:
                ds_by_key[key] = item

        # Track processed items to avoid duplicates
        processed_keys = set()
        merged_items = []

        # Process all CoinGecko items
        for item in cg_data:
            key = self._get_stable_key(item)
            if not key or key in processed_keys:
                continue

            # Find matching DexScreener item
            ds_item = ds_by_key.get(key)

            if ds_item:
                # Both sources present - merge with score mixing
                merged_item = self._merge_single_item(
                    item,
                    ds_item,
                    cg_data,
                    ds_data,
                )
                # Add sources array for provenance tracking
                merged_item["sources"] = ["coingecko", "dexscreener"]
                processed_keys.add(key)
                merged_items.append(merged_item)
            else:
                # Only CoinGecko - keep as-is but add source and ensure score
                item["source"] = "coingecko"
                item["sources"] = ["coingecko"]
                # Ensure score exists for normalization
                if "score" not in item:
                    item["score"] = 0.0
                processed_keys.add(key)
                merged_items.append(item)

        # Process remaining DexScreener items (not already matched)
        for item in ds_data:
            key = self._get_stable_key(item)
            if not key or key in processed_keys:
                continue

            item["source"] = "dexscreener"
            item["sources"] = ["dexscreener"]
            # Ensure score exists for normalization
            if "score" not in item:
                item["score"] = 0.0
            processed_keys.add(key)
            merged_items.append(item)

        # Log structured info per request
        counts = ContributionCounts(
            narrative=narrative,
            terms=terms,
            cg_data=cg_data,
            ds_data=ds_data,
            merged_items=merged_items,
        )
        self._log_contribution_counts(counts)

        return merged_items

    def _get_stable_key(self, item: dict) -> str | None:
        """Get a stable unique key for deduplication.

        Prefer mint/address, fallback to composite key not colliding on symbol.

        :param item: Item to generate key for.
        :return: Stable unique key or None if no valid key can be generated.
        """
        # Prefer mint/address combination
        address = item.get("address", "").strip().lower()
        chain = item.get("chain", "").strip().lower()

        if address and chain:
            return f"{chain}:{address}"

        # Fallback to composite key with symbol and name
        symbol = item.get("symbol", "").strip().lower()
        name = item.get("name", item.get("parent", "")).strip().lower()

        if symbol and name:
            return f"symbol:{symbol}:name:{name}"

        # Last resort: just symbol if available
        if symbol:
            return f"symbol:{symbol}"

        return None

    def _log_contribution_counts(self, counts: ContributionCounts) -> None:
        """Log structured contribution counts for debugging.

        :param counts: ContributionCounts data class with all parameters.
        """
        # Count items by source
        cg_count = len(counts.cg_data)
        ds_count = len(counts.ds_data)

        # Count merged items by source
        cg_only = 0
        ds_only = 0
        both = 0

        for item in counts.merged_items:
            sources = item.get("sources", [])
            if len(sources) == 2:
                both += 1
            elif "coingecko" in sources:
                cg_only += 1
            elif "dexscreener" in sources:
                ds_only += 1

        total = len(counts.merged_items)

        # Log structured info
        logger.info(
            "[MIXED] narrative=%s parent=%s window=24h cg_count=%d "
            "ds_count=%d cg_only=%d ds_only=%d both=%d total=%d",
            counts.narrative,
            counts.terms[0] if counts.terms else "unknown",
            cg_count,
            ds_count,
            cg_only,
            ds_only,
            both,
            total,
        )

    def _merge_single_item(
        self,
        cg_item: dict,
        ds_item: dict,
        cg_data: list[dict],
        ds_data: list[dict],
    ) -> dict:
        """Merge a single CoinGecko and DexScreener item.

        :param cg_item: CoinGecko item.
        :param ds_item: DexScreener item.
        :param cg_data: All CoinGecko data for normalization.
        :param ds_data: All DexScreener data for normalization.
        :return: Merged item.
        """
        # Get normalized volumes for score calculation
        cg_max_vol = self._get_max_volume_from_data(cg_data, "vol24h")
        ds_max_vol = self._get_max_volume_from_data(ds_data, "vol24h")

        cg_vol = cg_item.get("vol24h", 0) or 0
        ds_vol = ds_item.get("vol24h", 0) or 0

        cg_norm_vol = cg_vol / cg_max_vol if cg_max_vol > 0 else 0
        ds_norm_vol = ds_vol / ds_max_vol if ds_max_vol > 0 else 0

        # Calculate mixed score: 0.6 * CG + 0.4 * DS
        mixed_score = 0.6 * cg_norm_vol + 0.4 * ds_norm_vol

        # Prefer CoinGecko data for name/symbol/image/url, keep DexScreener
        # children
        merged_item = {
            "name": cg_item.get("name", ds_item.get("name", "")),
            "symbol": cg_item.get("symbol", ds_item.get("symbol", "")),
            "image": cg_item.get("image", ""),
            "url": cg_item.get("url", ds_item.get("url", "")),
            "marketCap": cg_item.get("marketCap", 0),
            "price": cg_item.get("price", 0),
            "vol24h": cg_item.get("vol24h", 0),
            "address": cg_item.get("address", ds_item.get("address", "")),
            "chain": ds_item.get("chain", ""),
            "source": "coingecko+dexscreener",
            "sources": ["coingecko", "dexscreener"],
            "score": mixed_score,
            "children": ds_item.get(
                "children",
                [],
            ),  # Keep DexScreener children pairs
        }

        return merged_item

    def _get_max_volume_from_data(
        self,
        data: list[dict],
        volume_key: str,
    ) -> float:
        """Get maximum volume from a dataset.

        :param data: List of data items.
        :param volume_key: Key to extract volume from.
        :return: Maximum volume value.
        """
        volumes = []
        for item in data:
            vol = item.get(volume_key, 0) or 0
            volumes.append(vol)
        return max(volumes) if volumes else 0

    def _renormalize_scores(self, items: list[dict]) -> list[dict]:
        """Re-normalize scores within the merged dataset.

        :param items: List of merged items.
        :return: Items with re-normalized scores.
        """
        if not items:
            return []

        # Get max score for normalization
        max_score = max(item.get("score", 0) for item in items)

        if max_score > 0:
            # Re-normalize all scores
            for item in items:
                item["score"] = item.get("score", 0) / max_score

        # Sort by score (descending) and return top 25
        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:25]
