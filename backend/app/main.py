from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import json

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

app = FastAPI(title="Narrative Heatmap API", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"ok": True}

def _read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path.name}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/narratives")
def get_narratives(window: str = "24h"):
    fname = f"narratives-{window}.json"
    payload = _read_json(DATA_DIR / fname)
    return JSONResponse(payload)

@app.get("/parents/{narrative}")
def get_parents(narrative: str, window: str = "24h"):
    fname = f"parents-{narrative}-{window}.json"
    payload = _read_json(DATA_DIR / fname)
    return JSONResponse(payload)
