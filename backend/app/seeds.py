import json, os
from functools import lru_cache
from typing import Any, Dict, List

DEFAULT_SEEDS_PATH = "/app/seeds/narratives.seed.json"

@lru_cache(maxsize=1)
def load_seeds() -> Dict[str, Any]:
    path = os.getenv("SEEDS_FILE", DEFAULT_SEEDS_PATH)
    with open(path, "r") as f:
        data = json.load(f)
    # normalize
    items = []
    for n in data.get("narratives", []):
        name = str(n.get("name", "")).strip()
        if not name:
            continue
        items.append({
            "name": name,
            "terms": list(n.get("terms", [])),
            "allowNameMatch": bool(n.get("allowNameMatch", True)),
            "block": list(n.get("block", [])),
        })
    return {"narratives": items}

def list_narrative_names() -> List[str]:
    return [n["name"] for n in load_seeds()["narratives"]]
