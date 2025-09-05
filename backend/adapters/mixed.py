"""Mixed adapter that merges DexScreener and CoinGecko data."""

from . import AdapterProtocol
from .coingecko import CoinGeckoAdapter
from .dexscreener import DexScreenerAdapter


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

        # Fetch data from both sources
        cg_data = self.cg_adapter.fetch_parents(narrative, terms)
        ds_data = self.ds_adapter.fetch_parents(narrative, terms)

        # Merge the data according to the specified rules
        merged_data = self._merge_data(cg_data, ds_data)

        # Re-normalize scores within the merged set
        return self._renormalize_scores(merged_data)

    def _merge_data(  # pylint: disable=too-many-locals,too-many-branches
        # pylint: disable=too-many-statements
        self,
        cg_data: list[dict],
        ds_data: list[dict],
    ) -> list[dict]:
        """Merge CoinGecko and DexScreener data by symbol/address.

        :param cg_data: CoinGecko parent data.
        :param ds_data: DexScreener parent data.
        :return: Merged parent data.
        """
        # Create lookup dictionaries indexed by symbol (case-insensitive) and
        # address
        cg_by_symbol = {}
        cg_by_address = {}
        ds_by_symbol = {}
        ds_by_address = {}

        # Index CoinGecko data
        for item in cg_data:
            symbol = item.get("symbol", "").lower()
            address = item.get("address", "").lower()
            if symbol:
                cg_by_symbol[symbol] = item
            if address:
                cg_by_address[address] = item

        # Index DexScreener data
        for item in ds_data:
            symbol = item.get("symbol", "").lower()
            address = item.get("address", "").lower()
            if symbol:
                ds_by_symbol[symbol] = item
            if address:
                ds_by_address[address] = item

        # Track processed items to avoid duplicates
        processed_keys = set()
        merged_items = []

        # Process all CoinGecko items
        for item in cg_data:
            symbol = item.get("symbol", "").lower()
            address = item.get("address", "").lower()

            # Find matching DexScreener item
            ds_item = None
            if symbol and symbol in ds_by_symbol:
                ds_item = ds_by_symbol[symbol]
            elif address and address in ds_by_address:
                ds_item = ds_by_address[address]

            if ds_item:
                # Both sources present - merge with score mixing
                merged_item = self._merge_single_item(
                    item,
                    ds_item,
                    cg_data,
                    ds_data,
                )
                key = f"{symbol}_{address}"
                if key not in processed_keys:
                    processed_keys.add(key)
                    # Also mark the DexScreener item as processed
                    ds_symbol = ds_item.get("symbol", "").lower()
                    ds_address = ds_item.get("address", "").lower()
                    ds_key = f"{ds_symbol}_{ds_address}"
                    processed_keys.add(ds_key)
                    merged_items.append(merged_item)
            else:
                # Only CoinGecko - keep as-is but add source and ensure score
                key = f"{symbol}_{address}"
                if key not in processed_keys:
                    processed_keys.add(key)
                    item["source"] = "coingecko"
                    # Ensure score exists for normalization
                    if "score" not in item:
                        item["score"] = 0.0
                    merged_items.append(item)

        # Process remaining DexScreener items (not already matched)
        for item in ds_data:
            symbol = item.get("symbol", "").lower()
            address = item.get("address", "").lower()
            key = f"{symbol}_{address}"

            if key not in processed_keys:
                processed_keys.add(key)
                item["source"] = "dexscreener"
                # Ensure score exists for normalization
                if "score" not in item:
                    item["score"] = 0.0
                merged_items.append(item)

        return merged_items

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
