"""DexScreener adapter for fetching parent data."""

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

        Currently a stub implementation that returns empty results.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: Empty list (stub implementation).
        """
        # TODO: Implement actual DexScreener API integration
        return []
