from __future__ import annotations
from typing import Dict, List, Any, Optional
import httpx
from ..config import HTTP_TIMEOUT, CHAIN_ID

DEX_SEARCH = "https://api.dexscreener.com/latest/dex/search"

class DexScreenerAdapter:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(timeout=HTTP_TIMEOUT, headers={"User-Agent": "narrative-heatmap/0.1"})

    def _search_pairs(self, query: str) -> List[Dict[str, Any]]:
        r = self.client.get(DEX_SEARCH, params={"q": query})
        r.raise_for_status()
        data = r.json()
        return data.get("pairs", []) or []

    def _prefer(self, pairs: List[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
        cands = [p for p in pairs if (p.get("chainId") or "").lower() == CHAIN_ID.lower()]
        exact = [p for p in cands if (p.get("baseToken") or {}).get("symbol", "").lower() == symbol.lower()]
        subset = exact or [p for p in cands if symbol.lower() in (p.get("baseToken") or {}).get("symbol", "").lower()]
        if not subset:
            return None
        return max(subset, key=lambda p: float(((p.get("liquidity") or {}).get("usd") or 0) or 0))

    def fetch_token_metrics(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for sym in symbols:
            pairs = self._search_pairs(sym)
            best = self._prefer(pairs, sym)
            if not best:
                out[sym] = {"volume24hUsd": 0.0, "liquidityUsd": 0.0}
                continue
            vol = float((best.get("volume", {}) or {}).get("h24") or 0.0)
            liq = float((best.get("liquidity") or {}).get("usd") or 0.0)
            out[sym] = {"volume24hUsd": vol, "liquidityUsd": liq}
        return out

    def fetch_children_for_parent(self, parent_symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        pairs = self._search_pairs(parent_symbol)[:200]
        out = []
        for p in pairs:
            base = (p.get("baseToken") or {}).get("symbol", "") or ""
            if (p.get("chainId") or "").lower() != CHAIN_ID.lower():
                continue
            if base.lower() == parent_symbol.lower():
                continue
            if parent_symbol.lower() not in base.lower():
                continue
            out.append({
                "symbol": base,
                "volume24hUsd": float((p.get("volume", {}) or {}).get("h24") or 0.0),
                "liquidityUsd": float((p.get("liquidity") or {}).get("usd") or 0.0),
                "pairCreatedAt": p.get("pairCreatedAt"),
                "holders": None,
            })
            if len(out) >= limit:
                break
        out.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        return out

def make_onchain_adapter(name: str = "dexscreener") -> DexScreenerAdapter:
    return DexScreenerAdapter()
