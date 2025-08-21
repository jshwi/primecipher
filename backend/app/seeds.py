from __future__ import annotations
from pathlib import Path
import json
from .config import SEED_DIR

def load_narrative_seeds():
    p = Path(SEED_DIR) / "narratives.seed.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return [
        { "narrative": "dogs", "keywords": ["wif","dog","moodeng"], "parents": ["WIF","MOODENG"] },
        { "narrative": "ai",   "keywords": ["ai","gpt","tao","fet"], "parents": ["FET","TAO"] }
    ]
