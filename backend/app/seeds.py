from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any
from .config import SEED_DIR

def _norm_discovery(d: Any) -> Dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    dex_ids = [str(x).lower() for x in (d.get("dexIds") or [])]
    def _num(key):
        v = d.get(key)
        try:
            return float(v) if v is not None else None
        except Exception:
            return None
    return {
        "dexIds": dex_ids,
        "volMinUsd": _num("volMinUsd"),
        "liqMinUsd": _num("liqMinUsd"),
        "maxAgeHours": _num("maxAgeHours"),
    }

def _norm_parent(p: Any) -> Dict[str, Any]:
    if isinstance(p, str):
        return {
            "symbol": p.upper(),
            "match": [p.lower()],
            "block": [],
            "nameMatchAllowed": True,
            "address": None,
            "discovery": {}
        }
    if isinstance(p, dict):
        sym = (p.get("symbol") or p.get("sym") or p.get("token") or "").upper()
        match = [m.lower() for m in (p.get("match") or ([sym.lower()] if sym else []))]
        block = [b.upper() for b in (p.get("block") or [])]
        addr = p.get("address")
        allow_name = bool(p.get("nameMatchAllowed", True))
        return {
            "symbol": sym,
            "match": match,
            "block": block,
            "address": addr,
            "nameMatchAllowed": allow_name,
            "discovery": _norm_discovery(p.get("discovery") or {})
        }
    return {}

def _normalize_seed(seed: Dict[str, Any]) -> Dict[str, Any]:
    parents = seed.get("parents", [])
    norm_parents = [_norm_parent(p) for p in parents]
    out = dict(seed)
    out["parents"] = [p for p in norm_parents if p.get("symbol")]
    return out

def load_narrative_seeds() -> List[Dict[str, Any]]:
    p = Path(SEED_DIR) / "narratives.seed.json"
    if p.exists():
        raw = json.loads(p.read_text(encoding="utf-8"))
    else:
        raw = [
            {"narrative":"dogs","keywords":["wif","dog","moodeng"],"parents":["WIF","MOODENG"]},
            {"narrative":"ai","keywords":["ai","gpt","tao","fet"],"parents":["FET","TAO"]},
        ]
    return [_normalize_seed(s) for s in raw]

