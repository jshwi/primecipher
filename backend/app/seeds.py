from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .schemas import SeedsV2


def _seeds_path() -> Path:
    # Single source of truth; override in tests/dev with SEEDS_PATH.
    env = os.getenv("SEEDS_PATH")
    if env:
        return Path(env)
    return Path("backend/seeds/narratives.seed.json")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_seeds() -> SeedsV2:
    """
    Load and cache v2 seeds. No legacy support.
    """
    raw = _read_json(_seeds_path())
    if not isinstance(raw, dict) or raw.get("version") != 2:
        raise ValueError("Seeds must be version=2 JSON object")
    return SeedsV2.model_validate(raw)


def reload_seeds() -> SeedsV2:
    """
    Clear cache and reload (used by /seeds/reload and tests).
    """
    get_seeds.cache_clear()  # type: ignore[attr-defined]
    return get_seeds()


def list_narrative_names() -> list[str]:
    return [n.name for n in get_seeds().narratives]
