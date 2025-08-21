# backend/app/main.py
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from datetime import datetime, timezone

from .config import DATA_DIR, SEED_DIR, PROVIDER
from .seeds import load_narrative_seeds
from .compute import compute_heat
from .parents import build_parent_ecosystems
from .adapters.onchain import make_onchain_adapter

DATA = Path(DATA_DIR)
SEEDS = Path(SEED_DIR)
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Narrative Heatmap API", version="0.2.0")

def _read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def build_live_narratives(window: str = "24h"):
    seeds = load_narrative_seeds()
    adapter = make_onchain_adapter(PROVIDER)

    # fetch metrics for all parent symbols
    all_parents = []
    for s in seeds:
        all_parents.extend(s.get("parents", []))
    all_parents = list(dict.fromkeys(all_parents))  # dedupe

    metrics = adapter.fetch_token_metrics(all_parents) if all_parents else {}

    # build narrative payloads by summing parent metrics
    narratives = []
    for s in seeds:
        parents = s.get("parents", [])
        sum_vol = sum((metrics.get(p, {}).get("volume24hUsd") or 0.0) for p in parents)
        sum_liq = sum((metrics.get(p, {}).get("liquidityUsd") or 0.0) for p in parents)
        n = {
            "narrative": s["narrative"],
            "heatScore": 0.0,  # replaced by compute_heat
            "window": window,
            "signals": {
                "onchainVolumeUsd": float(sum_vol),
                "onchainLiquidityUsd": float(sum_liq),
                "ctMentions": 0
            },
            "parents": parents,
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
    parents = seed.get("parents", []) or []
    rows = build_parent_ecosystems(narrative, parents, adapter)
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

    # write parent files per narrative
    for n in narratives:
        rows = build_live_parents(n["narrative"], window=window)
        _write_json(DATA / f"parents-{n['narrative']}-{window}.json", rows)

    return {"ok": True, "updated": [p["narrative"] for p in narratives]}

@app.get("/narratives")
def get_narratives(window: str = "24h", source: str = "file"):
    if source == "live":
        narratives = build_live_narratives(window=window)
        return JSONResponse(narratives)
    fname = f"narratives-{window}.json"
    payload = _read_json(DATA / fname)
    return JSONResponse(payload)

@app.get("/parents/{narrative}")
def get_parents(narrative: str, window: str = "24h", source: str = "file"):
    if source == "live":
        rows = build_live_parents(narrative, window=window)
        return JSONResponse(rows)
    fname = f"parents-{narrative}-{window}.json"
    payload = _read_json(DATA / fname)
    return JSONResponse(payload)

