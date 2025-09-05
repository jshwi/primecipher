"""CoinGecko adapter for fetching parent data."""

from . import AdapterProtocol


class CoinGeckoAdapter(
    AdapterProtocol,
):  # pylint: disable=too-few-public-methods
    """Adapter for CoinGecko data source."""

    def fetch_parents(self, narrative: str, terms: list[str]) -> list[dict]:
        """Fetch parent data from CoinGecko.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: List of parent dictionaries (stub implementation).
        """
        # Stub implementation - returns empty list for now
        return []
