from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime, timezone

from .config import DATA_DIR, SEED_DIR, PROVIDER
from .seeds import load_narrative_seeds
from .compute import compute_heat
from .parents import build_parent_ecosystems
from .adapters.onchain import make_onchain_adapter
from .debug import router as debug_router
from .config import CORS_ALLOW_ORIGINS


DATA = Path(DATA_DIR)
SEEDS = Path(SEED_DIR)
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Narrative Heatmap API", version="0.2.2")

app.include_router(debug_router, prefix="/debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ALLOW_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

def _read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _parent_objs(seed_entry) -> list[dict]:
    return [p for p in (seed_entry.get("parents") or []) if isinstance(p, dict) and p.get("symbol")]

def _parent_symbols(seed_entry) -> list[str]:
    seen = set(); out = []
    for p in _parent_objs(seed_entry):
        s = p["symbol"]
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def build_live_narratives(window: str = "24h"):
    seeds = load_narrative_seeds()
    adapter = make_onchain_adapter(PROVIDER)

    # collect all parent objects across seeds (to use addresses)
    all_parent_objs = []
    seen = set()
    for s in seeds:
        for p in _parent_objs(s):
            key = p["symbol"]
            if key not in seen:
                seen.add(key)
                all_parent_objs.append(p)

    metrics = adapter.fetch_parent_metrics(all_parent_objs) if all_parent_objs else {}

    narratives = []
    for s in seeds:
        parents_syms = _parent_symbols(s)
        sum_vol = sum((metrics.get(p, {}).get("volume24hUsd") or 0.0) for p in parents_syms)
        sum_liq = sum((metrics.get(p, {}).get("liquidityUsd") or 0.0) for p in parents_syms)
        n = {
            "narrative": s["narrative"],
            "heatScore": 0.0,
            "window": window,
            "signals": {
                "onchainVolumeUsd": float(sum_vol),
                "onchainLiquidityUsd": float(sum_liq),
                "ctMentions": 0
            },
            "parents": parents_syms,
            "lastUpdated": _now_iso(),
        }
        narratives.append(n)

    return compute_heat(narratives)

def build_live_parents(narrative: str, window: str = "24h"):
    seeds = load_narrative_seeds()
    seed = next((s for s in seeds if s.get("narrative") == narrative), None)
    if not seed:
        return []
    adapter = make_onchain_adapter(PROVIDER)
    parents_objs = _parent_objs(seed)
    # nameMatchAllowed handled in parents.py
    rows = build_parent_ecosystems(narrative, parents_objs, adapter)
    for r in rows:
        r["lastUpdated"] = _now_iso()
    return rows

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/refresh")
def refresh(window: str = Query("24h")):
    narratives = build_live_narratives(window=window)
    _write_json(DATA / f"narratives-{window}.json", narratives)
    for n in narratives:
        rows = build_live_parents(n["narrative"], window=window)
        _write_json(DATA / f"parents-{n['narrative']}-{window}.json", rows)
    return {"ok": True, "updated": [p["narrative"] for p in narratives]}

@app.get("/narratives")
def get_narratives(window: str = "24h", source: str = "file"):
    if source == "live":
        return JSONResponse(build_live_narratives(window=window))
    return JSONResponse(_read_json(DATA / f"narratives-{window}.json"))

@app.get("/parents/{narrative}")
def get_parents(narrative: str, window: str = "24h", source: str = "file"):
    if source == "live":
        return JSONResponse(build_live_parents(narrative, window=window))
    return JSONResponse(_read_json(DATA / f"parents-{narrative}-{window}.json"))

