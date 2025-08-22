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

    def _filter_pairs(self, pairs: List[Dict[str, Any]], *, min_vol: float, min_liq: float, dex_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        allow = dex_ids or DEX_IDS
        out = []
        for p in pairs:
            if (p.get("chainId") or "").lower() != CHAIN_ID:
                continue
            dex = (p.get("dexId") or "").lower()
            if dex and allow and dex not in allow:
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
        if address:
            addr_l = address.lower()
            addr_hits = [p for p in flt if ((p.get("baseToken") or {}).get("address","").lower() == addr_l)]
            if addr_hits:
                return max(addr_hits, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))
        norm_target = _norm_alnum_upper(symbol)
        exact = [p for p in flt if _norm_alnum_upper((p.get("baseToken") or {}).get("symbol")) == norm_target]
        pool = exact or flt
        return max(pool, key=lambda p: float((p.get("volume") or {}).get("h24") or 0.0))

    def fetch_parent_metrics(self, parents: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for p in parents:
            sym = p.get("symbol")
            addr = p.get("address")
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

    def fetch_children_for_parent(
        self,
        parent_symbol: str,
        match_terms: List[str],
        allow_name_match: bool = True,
        limit: int = 50,
        discovery: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        norm_parent = _norm_alnum_upper(parent_symbol)
        # dedupe + keep order
        terms = []
        seen_t = set()
        for t in ([parent_symbol] + (match_terms or [])):
            if not t: continue
            tl = t.lower()
            if tl not in seen_t:
                seen_t.add(tl); terms.append(t)

        dex_ids = set((discovery or {}).get("dexIds") or []) or None
        vol_min = (discovery or {}).get("volMinUsd")
        liq_min = (discovery or {}).get("liqMinUsd")
        max_age = (discovery or {}).get("maxAgeHours")
        require_all = bool((discovery or {}).get("requireAllTerms", False))

        vol_floor = float(vol_min) if vol_min is not None else CHILD_VOL_MIN_USD
        liq_floor = float(liq_min) if liq_min is not None else CHILD_LIQ_MIN_USD
        max_age_h = float(max_age) if max_age is not None else CHILD_MAX_AGE_HOURS

        out: List[Dict[str, Any]] = []
        seen_addr: Set[str] = set()

        for term in terms:
            pairs = self._filter_pairs(
                self._search_pairs(term),
                min_vol=vol_floor,
                min_liq=liq_floor,
                dex_ids=dex_ids,
            )
            for p in pairs:
                base = (p.get("baseToken") or {})
                sym_raw = base.get("symbol") or ""
                name_raw = base.get("name") or ""
                addr = base.get("address") or p.get("pairAddress") or ""
                if not addr or addr in seen_addr:
                    continue
                # exclude parent itself
                if _norm_alnum_upper(sym_raw) == norm_parent:
                    continue

                sym = sym_raw.lower()
                name = name_raw.lower()

                matched_terms: List[str] = []
                matched_where: List[str] = []
                for t in terms:
                    tl = t.lower()
                    sym_hit = (tl in sym)
                    name_hit = allow_name_match and (len(tl) >= 5) and (tl in name)
                    if sym_hit or name_hit:
                        matched_terms.append(t)
                        matched_where.append("symbol" if sym_hit and not name_hit else ("name" if name_hit and not sym_hit else "mixed"))

                if require_all and not all(t in [mt.lower() for mt in matched_terms] for t in [tt.lower() for tt in terms]):
                    continue
                if not require_all and not matched_terms:
                    continue

                seen_addr.add(addr)
                where_field = "mixed"
                if matched_where and all(w == "symbol" for w in matched_where):
                    where_field = "symbol"
                elif matched_where and all(w == "name" for w in matched_where):
                    where_field = "name"

                out.append({
                    "symbol": sym_raw,
                    "name": name_raw,
                    "volume24hUsd": float((p.get("volume") or {}).get("h24") or 0.0),
                    "liquidityUsd": float((p.get("liquidity") or {}).get("usd") or 0.0),
                    "pairCreatedAt": p.get("pairCreatedAt"),
                    "ageHours": _age_hours_ms(p.get("pairCreatedAt")),
                    "holders": None,
                    "matched": {
                        "field": where_field,
                        "term": matched_terms[0] if matched_terms else None,
                        "terms": matched_terms,
                        "dexId": p.get("dexId"),
                        "pairAddress": p.get("pairAddress"),
                    },
                })

        recent = [c for c in out if (c.get("ageHours") or 1e9) <= max_age_h]
        rest = [c for c in out if c not in recent]
        recent.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        rest.sort(key=lambda x: x["volume24hUsd"], reverse=True)
        return (recent + rest)[:limit]

def make_onchain_adapter(name: str = "dexscreener") -> DexScreenerAdapter:
    return DexScreenerAdapter()

