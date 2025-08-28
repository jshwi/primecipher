from typing import Dict, List
from time import time

# Simulated store refreshed by /refresh (no DB — MVP)
_parents: Dict[str, List[dict]] = {}
_last_refresh_ts: float = 0.0

def set_parents(narrative: str, parents: List[dict]) -> None:
    global _parents
    _parents[narrative] = parents

def get_parents(narrative: str) -> List[dict]:
    return _parents.get(narrative, [])

def mark_refreshed() -> None:
    global _last_refresh_ts
    _last_refresh_ts = time()

def last_refresh_ts() -> float:
    return _last_refresh_ts
