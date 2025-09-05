"""CoinGecko adapter for fetching parent data."""

import logging
import time

import httpx

from . import AdapterProtocol


class CoinGeckoAdapter(
    AdapterProtocol,
):  # pylint: disable=too-few-public-methods
    """Adapter for CoinGecko data source."""

    def fetch_parents(self, narrative: str, terms: list[str]) -> list[dict]:
        """Fetch parent data from CoinGecko.

        :param narrative: The narrative name.
        :param terms: List of search terms.
        :return: List of raw market data rows.
        """
        try:
            # Use up to first 3 seed terms per narrative
            search_terms = (terms or [])[:3]
            if not search_terms:
                return []

            # Collect coin IDs from search API
            coin_ids = self._search_coins(search_terms)
            if not coin_ids:
                return []

            # Fetch market data for the coin IDs
            market_data = self._get_market_data(coin_ids)
            if not market_data:
                return []

            # Format and return raw market data with requested fields
            parents = self._format_raw_market_data(market_data)
            # Log final mapped parents count
            logging.info("[CG] parents mapped=%s", len(parents))
            return parents

        except Exception:  # pylint: disable=broad-exception-caught
            # Return empty list on any error
            return []

    def _search_coins(self, terms: list[str]) -> list[str]:
        """Search for coins using terms and collect coin IDs.

        :param terms: List of search terms.
        :return: List of unique coin IDs.
        """
        coin_ids = set()

        for term in terms:
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
                # Limit to ~10 per term
                for coin in coins[:10]:
                    coin_id = coin.get("id")
                    if coin_id:
                        coin_ids.add(coin_id)

                # Log search results for this term
                ids_count = len([c for c in coins[:10] if c.get("id")])
                logging.info("[CG] term=%s ids=%s", term, ids_count)

            except Exception:  # pylint: disable=broad-exception-caught
                # Continue with other terms if one fails
                continue

        # Cap total ids ~30/narrative
        return list(coin_ids)[:30]

    def _get_market_data(self, coin_ids: list[str]) -> list[dict]:
        """Get detailed market data for coin IDs.

        :param coin_ids: List of coin IDs to fetch data for.
        :return: List of market data dictionaries.
        """
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
            logging.info("[CG] markets rows=%s", len(rows))
            return rows

        except Exception:  # pylint: disable=broad-exception-caught
            return []

    def _format_parents(self, market_data: list[dict]) -> list[dict]:
        """Format market data into parent dictionaries with scoring.

        :param market_data: List of market data from CoinGecko API.
        :return: List of formatted parent dictionaries.
        """
        if not market_data:
            return []

        # Calculate normalized scores based on vol24h
        volumes = [item.get("total_volume", 0) or 0 for item in market_data]
        max_volume = max(volumes) if volumes and max(volumes) > 0 else 1

        parents = []
        for item in market_data:
            coin_id = item.get("id", "")
            if not coin_id:
                continue

            volume = item.get("total_volume", 0) or 0
            score = volume / max_volume if max_volume > 0 else 0

            parent = {
                "name": item.get("name", ""),
                "symbol": item.get("symbol", ""),
                "source": "coingecko",
                "url": f"https://www.coingecko.com/en/coins/{coin_id}",
                "image": item.get("image", ""),
                "marketCap": item.get("market_cap", 0) or 0,
                "vol24h": volume,
                "price": item.get("current_price", 0) or 0,
                "score": score,
                "children": [
                    {
                        "url": f"https://www.coingecko.com/en/coins/{coin_id}",
                        "evidence": "coingecko_page",
                    },
                ],
            }
            parents.append(parent)

        # Sort by score (descending) and return top 25
        parents.sort(key=lambda x: x["score"], reverse=True)
        return parents

    def _format_raw_market_data(self, market_data: list[dict]) -> list[dict]:
        """Format market data into raw rows with requested fields.

        :param market_data: List of market data from CoinGecko API.
        :return: List of raw market data rows with fields: name, symbol, image,
            current_price, market_cap, total_volume, id.
        """
        if not market_data:
            return []

        raw_rows = []
        for item in market_data:
            raw_row = {
                "name": item.get("name", ""),
                "symbol": item.get("symbol", ""),
                "image": item.get("image", ""),
                "current_price": item.get("current_price", 0) or 0,
                "market_cap": item.get("market_cap", 0) or 0,
                "total_volume": item.get("total_volume", 0) or 0,
                "id": item.get("id", ""),
            }
            raw_rows.append(raw_row)

        return raw_rows
