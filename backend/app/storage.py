"""In-memory storage for parent data and refresh timestamps."""

from time import time

# simulated store refreshed by /refresh (no db — mvp)
_parents: dict[str, list[dict]] = {}
_last_refresh_ts: float = 0.0


def set_parents(narrative: str, parents: list[dict]) -> None:
    """Set parent data for a narrative.

    :param narrative: The narrative to set parent data for.
    :param parents: The parent data to set.
    """
    _parents[narrative] = parents


def get_parents(narrative: str) -> list[dict]:
    """Get parent data for a narrative.

    :param narrative: The narrative to get parent data for.
    :return: The parent data for the narrative.
    """
    return _parents.get(narrative, [])


def mark_refreshed() -> None:
    """Mark the last refresh timestamp."""
    global _last_refresh_ts  # noqa: W0602
    _last_refresh_ts = time()


def last_refresh_ts() -> float:
    """Get the last refresh timestamp.

    :return: The last refresh timestamp.
    """
    return _last_refresh_ts
