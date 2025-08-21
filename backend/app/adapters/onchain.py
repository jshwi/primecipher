# backend/app/adapters/onchain.py
from __future__ import annotations
from typing import Dict, List, Any, Optional, Set
import httpx
from ..config import HTTP_TIMEOUT, CHAIN_ID, DEX_IDS, LIQ_MAX_USD, VOL_MIN_USD

DEX_SEARCH = "https://api.dexscreener.com/latest/dex/search"

class DexScreenerAdapter:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "narrative-heatmap/0.2"}
        )

    def _search_pairs(self, query: str) -> List[Dict[str, Any]]:
        r = self.client.get(DEX_SEARCH, params={"q": query})
        r.raise_for_status()
        data = r.json()
        return data.get("pairs", []) or []

    def _filter_pairs(self, pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for p in pairs:
            if (p.get("chainId") or "").lower() != CHAIN_ID:
                continue
            dex = (p.get("dexId") or "").lower()
            if dex and DEX_IDS and dex not in DEX_IDS:
                continue
            liq = float((p.get("liquidity") or {}).get("usd") or 0.0)
            vol = float((p.get("volume") or {}).get("h24") or 0.0)
            if liq <= 0 or vol < VOL_MIN_USD or liq > LIQ_MAX_USD:
                continue
            out.append(p)
        return out

    def _prefer(self, pairs: List[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
        flt = self._filter_pairs(pairs)
        if not flt:
            return None
        exact = [p for p in flt if (p.get("baseToken") or {}).get("symbol", "").lower() == symbol.lower()]
        pool = exact or flt
        return max(pool, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))

    def fetch_token_metrics(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for sym in symbols:
            pairs = self._search_pairs(sym)
            best = self._prefer(pairs, sym)
            if not best:
                out[sym] = {"volume24hUsd": 0.0, "liquidityUsd": 0.0}
                continue
            vol = float((best.get("volume") or {}).get("h24") or 0.0)
            liq = float((best.get("liquidity") or {}).get("usd") or 0.0)
            out[sym] = {"volume24hUsd": vol, "liquidityUsd": liq}
        return out

    def fetch_children_for_parent(self, parent_symbol: str, match_terms: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        terms = list({(parent_symbol or "").lower(), *(t.lower() for t in (match_terms or []))})
        seen: Set[str] = set()
        children: List[Dict[str, Any]] = []

        # search for each term and merge
        for term in terms:
            pairs = self._filter_pairs(self._search_pairs(term))
            for p in pairs:
                base = (p.get("baseToken") or {})
                sym = (base.get("symbol") or "").lower()
                name = (base.get("name") or "").lower()
                addr = (base.get("address") or "") or (p.get("baseToken") or {}).get("address") or (p.get("pairAddress") or "")
                if sym == (parent_symbol or "").lower():
                    continue
                # require any term in symbol OR name
                if not any(t in sym or t in name for t in terms):
                    continue
                if addr and addr in seen:
                    continue
                seen.add(addr)
                children.append({
                    "symbol": base.get("symbol") or "",
                    "name": base.get("name") or "",
                    "volume24hUsd": float((p.get("volume") or {}).get("h24") or 0.0),
                    "liquidityUsd": float((p.get("liquidity") or {}).get("usd") or 0.0),
                    "pairCreatedAt": p.get("pairCreatedAt"),
                    "holders": None,
                })

        children.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        return children[:limit]

def make_onchain_adapter(name: str = "dexscreener") -> DexScreenerAdapter:
    return DexScreenerAdapter()

