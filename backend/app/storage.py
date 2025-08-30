from time import time

# Simulated store refreshed by /refresh (no DB — MVP)
_parents: dict[str, list[dict]] = {}
_last_refresh_ts: float = 0.0


def set_parents(narrative: str, parents: list[dict]) -> None:
    global _parents
    _parents[narrative] = parents


def get_parents(narrative: str) -> list[dict]:
    return _parents.get(narrative, [])


def mark_refreshed() -> None:
    global _last_refresh_ts
    _last_refresh_ts = time()


def last_refresh_ts() -> float:
    return _last_refresh_ts
