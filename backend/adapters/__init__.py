"""Adapters package for data source integration."""

from abc import ABC, abstractmethod


class AdapterProtocol(ABC):  # pylint: disable=too-few-public-methods
    """Protocol for data source adapters."""

    @abstractmethod
    def fetch_parents(self, narrative: str, terms: list[str]) -> list[dict]:
        """Fetch parent data for a narrative.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: List of parent dictionaries.
        """


class NoopAdapter(AdapterProtocol):  # pylint: disable=too-few-public-methods
    """No-op adapter that returns empty results."""

    def fetch_parents(self, narrative: str, terms: list[str]) -> list[dict]:
        """Return empty list for any narrative.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: Empty list.
        """
        return []


# Registry of available adapters
REGISTRY: dict[str, type[AdapterProtocol]] = {}


def get_adapter(mode: str) -> AdapterProtocol:  # pragma: no cover
    """Get an adapter instance based on mode.

    :param mode: The mode to get adapter for.
    :return: Adapter instance.
    """
    if mode == "real_cg":
        # Import here to avoid circular imports
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .coingecko import CoinGeckoAdapter

        return CoinGeckoAdapter()
    if mode == "real":
        # Import here to avoid circular imports
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .dexscreener import DexScreenerAdapter

        return DexScreenerAdapter()
    if mode == "real_mix":
        # Import here to avoid circular imports
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .mixed import MixedAdapter

        return MixedAdapter()
    return NoopAdapter()
