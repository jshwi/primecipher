from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
SEEDS = ROOT / "seeds"

def load_narrative_seeds():
    p = SEEDS / "narratives.seed.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
