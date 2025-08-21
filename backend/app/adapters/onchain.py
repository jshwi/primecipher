from __future__ import annotations
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
import httpx
from ..config import (
    HTTP_TIMEOUT, CHAIN_ID, DEX_IDS,
    LIQ_MAX_USD, VOL_MIN_USD,
    CHILD_VOL_MIN_USD, CHILD_LIQ_MIN_USD, CHILD_MAX_AGE_HOURS,
)

DEX_SEARCH = "https://api.dexscreener.com/latest/dex/search"

def _norm_symbol(s: Optional[str]) -> str:
    # Remove non-alphanumerics and uppercase so "$WIF" == "WIF"
    return "".join(ch for ch in (s or "") if ch.isalnum()).upper()

def _age_hours_ms(created_ms: Optional[int]) -> Optional[float]:
    if not created_ms:
        return None
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return max(0.0, (now_ms - int(created_ms)) / 3_600_000.0)

class DexScreenerAdapter:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "narrative-heatmap/0.3"}
        )

    def _search_pairs(self, query: str) -> List[Dict[str, Any]]:
        r = self.client.get(DEX_SEARCH, params={"q": query})
        r.raise_for_status()
        data = r.json()
        return data.get("pairs", []) or []

    def _filter_pairs(self, pairs: List[Dict[str, Any]], *, min_vol: float, min_liq: float) -> List[Dict[str, Any]]:
        out = []
        for p in pairs:
            if (p.get("chainId") or "").lower() != CHAIN_ID:
                continue
            dex = (p.get("dexId") or "").lower()
            if dex and DEX_IDS and dex not in DEX_IDS:
                continue
            liq = float((p.get("liquidity") or {}).get("usd") or 0.0)
            vol = float((p.get("volume") or {}).get("h24") or 0.0)
            if liq <= 0 or vol < min_vol or liq > LIQ_MAX_USD:
                continue
            out.append(p)
        return out

    def _prefer_parent_pair(self, pairs: List[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
        flt = self._filter_pairs(pairs, min_vol=VOL_MIN_USD, min_liq=1.0)
        if not flt:
            return None
        norm_target = _norm_symbol(symbol)
        exact = [p for p in flt if _norm_symbol((p.get("baseToken") or {}).get("symbol")) == norm_target]
        pool = exact or flt
        return max(pool, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))

    def fetch_token_metrics(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for sym in symbols:
            pairs = self._search_pairs(sym)
            best = self._prefer_parent_pair(pairs, sym)
            if not best:
                out[sym] = {"volume24hUsd": 0.0, "liquidityUsd": 0.0}
                continue
            vol = float((best.get("volume") or {}).get("h24") or 0.0)
            liq = float((best.get("liquidity") or {}).get("usd") or 0.0)
            out[sym] = {"volume24hUsd": vol, "liquidityUsd": liq}
        return out

    def fetch_children_for_parent(self, parent_symbol: str, match_terms: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        norm_parent = _norm_symbol(parent_symbol)
        terms = list({t.lower() for t in ([parent_symbol] + (match_terms or []))})
        seen: Set[str] = set()
        children: List[Dict[str, Any]] = []

        for term in terms:
            pairs = self._filter_pairs(
                self._search_pairs(term),
                min_vol=CHILD_VOL_MIN_USD,
                min_liq=CHILD_LIQ_MIN_USD,
            )
            for p in pairs:
                base = (p.get("baseToken") or {})
                sym_raw = base.get("symbol") or ""
                name_raw = base.get("name") or ""
                addr = base.get("address") or p.get("pairAddress") or ""
                if not addr or addr in seen:
                    continue
                # exclude the parent itself (handles "$WIF" vs "WIF")
                if _norm_symbol(sym_raw) == norm_parent:
                    continue
                sym = sym_raw.lower()
                name = name_raw.lower()
                if not any(t in sym or t in name for t in terms):
                    continue
                children.append({
                    "symbol": sym_raw,
                    "name": name_raw,
                    "volume24hUsd": float((p.get("volume") or {}).get("h24") or 0.0),
                    "liquidityUsd": float((p.get("liquidity") or {}).get("usd") or 0.0),
                    "pairCreatedAt": p.get("pairCreatedAt"),
                    "ageHours": _age_hours_ms(p.get("pairCreatedAt")),
                    "holders": None,
                })
                seen.add(addr)

        children.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        # prioritize recent within CHILD_MAX_AGE_HOURS
        recent = [c for c in children if (c.get("ageHours") or 1e9) <= CHILD_MAX_AGE_HOURS]
        rest = [c for c in children if c not in recent]
        return (recent + rest)[:limit]

def make_onchain_adapter(name: str = "dexscreener") -> DexScreenerAdapter:
    return DexScreenerAdapter()

