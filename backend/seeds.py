"""Seed data loading and management."""

import json
import os
from functools import lru_cache
from typing import Any

DEFAULT_SEEDS_PATH = "/app/seeds/narratives.seed.json"


@lru_cache(maxsize=1)
def load_seeds() -> dict[str, Any]:
    """Load and normalize seed data from JSON file.

    :return: Normalized seed data.
    """
    path = os.getenv("SEEDS_FILE", DEFAULT_SEEDS_PATH)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # normalize
    items = []
    for n in data.get("narratives", []):
        name = str(n.get("name", "")).strip()
        if not name:
            continue
        items.append(
            {
                "name": name,
                "terms": list(n.get("terms", [])),
                "allowNameMatch": bool(n.get("allowNameMatch", True)),
                "block": list(n.get("block", [])),
            },
        )
    return {"narratives": items}


def list_narrative_names() -> list[str]:
    """Get list of narrative names from seeds.

    :return: List of narrative names.
    """
    return [n["name"] for n in load_seeds()["narratives"]]
