from __future__ import annotations
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import httpx
from ..config import (
    HTTP_TIMEOUT, CHAIN_ID, DEX_IDS,
    LIQ_MAX_USD, VOL_MIN_USD,
    CHILD_VOL_MIN_USD, CHILD_LIQ_MIN_USD, CHILD_MAX_AGE_HOURS,
)

DEX_SEARCH = "https://api.dexscreener.com/latest/dex/search"

def _norm_alnum_upper(s: Optional[str]) -> str:
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

    # ---------- Parent metrics ----------
    def _prefer_parent_pair(self, pairs: List[Dict[str, Any]], symbol: str, address: Optional[str]) -> Optional[Dict[str, Any]]:
        flt = self._filter_pairs(pairs, min_vol=VOL_MIN_USD, min_liq=1.0)
        if not flt:
            return None
        # 1) prefer exact base address match when provided
        if address:
            addr_l = address.lower()
            addr_hits = [p for p in flt if ((p.get("baseToken") or {}).get("address","").lower() == addr_l)]
            if addr_hits:
                return max(addr_hits, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))
        # 2) else prefer exact base symbol
        norm_target = _norm_alnum_upper(symbol)
        exact = [p for p in flt if _norm_alnum_upper((p.get("baseToken") or {}).get("symbol")) == norm_target]
        pool = exact or flt
        # 3) rank by 24h volume
        return max(pool, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))

    def fetch_parent_metrics(self, parents: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        parents: [{symbol, address?}, ...]
        Returns {symbol: {volume24hUsd, liquidityUsd}}
        """
        out: Dict[str, Dict[str, float]] = {}
        for p in parents:
            sym = p.get("symbol")
            addr = p.get("address")
            # try address as query first (dexscreener supports address in search),
            # fall back to symbol
            queries = [q for q in [addr, sym] if q]
            best = None
            for q in queries:
                pairs = self._search_pairs(q)
                cand = self._prefer_parent_pair(pairs, symbol=sym or "", address=addr)
                if cand:
                    best = cand
                    break
            if not best:
                out[sym] = {"volume24hUsd": 0.0, "liquidityUsd": 0.0}
                continue
            vol = float((best.get("volume") or {}).get("h24") or 0.0)
            liq = float((best.get("liquidity") or {}).get("usd") or 0.0)
            out[sym] = {"volume24hUsd": vol, "liquidityUsd": liq}
        return out

    # ---------- Child discovery ----------
    def _match_terms_debug(self, symbol: str, name: str, terms: List[str]) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Symbol-first matching; allow name matches only for longer terms (>=5 chars).
        Returns (matched?, debug_info).
        """
        sym_l = (symbol or "").lower()
        name_l = (name or "").lower()

        for t in terms:
            t_l = t.lower()
            if t_l in sym_l:
                return True, {"field": "symbol", "term": t}
        for t in terms:
            if len(t) >= 5 and t.lower() in name_l:
                return True, {"field": "name", "term": t}
        return False, None

    def fetch_children_for_parent(self, parent_symbol: str, match_terms: List[str], allow_name_match: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        norm_parent = _norm_alnum_upper(parent_symbol)
        terms = list({t for t in ([parent_symbol] + (match_terms or [])) if t})
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
                # Exclude the parent itself (handles "$WIF" vs "WIF")
                if _norm_alnum_upper(sym_raw) == norm_parent:
                    continue

                # symbol-first; name allowed only if flag is true and term is long
                sym = sym_raw.lower()
                name = name_raw.lower()
                sym_hit = any(t.lower() in sym for t in terms)
                name_hit = allow_name_match and any(len(t) >= 5 and t.lower() in name for t in terms)
                if not (sym_hit or name_hit):
                    continue

                seen.add(addr)
                children.append({
                    "symbol": sym_raw,
                    "name": name_raw,
                    "volume24hUsd": float((p.get("volume") or {}).get("h24") or 0.0),
                    "liquidityUsd": float((p.get("liquidity") or {}).get("usd") or 0.0),
                    "pairCreatedAt": p.get("pairCreatedAt"),
                    "ageHours": _age_hours_ms(p.get("pairCreatedAt")),
                    "holders": None,
                    "matched": {
                        "field": "symbol" if sym_hit else "name",
                        "term": next((t for t in terms if (t.lower() in sym) or (allow_name_match and len(t) >= 5 and t.lower() in name)), None),
                        "dexId": p.get("dexId"),
                        "pairAddress": p.get("pairAddress"),
                    },
                })

        # Order: recent first, then by 24h volume
        recent = [c for c in children if (c.get("ageHours") or 1e9) <= CHILD_MAX_AGE_HOURS]
        rest = [c for c in children if c not in recent]
        recent.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        rest.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        return (recent + rest)[:limit]

def make_onchain_adapter(name: str = "dexscreener") -> DexScreenerAdapter:
    return DexScreenerAdapter()

