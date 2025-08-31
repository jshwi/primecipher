"""Parent computation and scoring functionality."""

from math import sqrt
from time import time

from .adapters.source import Source
from .repo import replace_parents
from .schemas import Parent
from .seeds import load_seeds
from .storage import set_parents

TOP_N = 100  # new


def _validate_items(items: list[dict]) -> list[dict]:
    return [Parent(**it).model_dump() for it in items]


# new: z-score per narrative, clamped to [-3, 3]
def _with_scores(items: list[dict]) -> list[dict]:
    if not items:
        return items
    xs = [int(it["matches"]) for it in items]
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / len(xs)
    std = sqrt(var)
    out: list[dict] = []
    for it in items:
        if std == 0:
            z = 0.0
        else:
            z = (int(it["matches"]) - mean) / std
            # clamp
            z = 3.0 if z > 3 else -3.0 if z < -3 else z
        it2 = dict(it)
        it2["score"] = float(round(z, 4))
        out.append(it2)
    # sort by score desc, then matches desc, then parent asc
    out.sort(
        key=lambda r: (
            -float(r.get("score") or 0.0),
            -int(r["matches"]),
            str(r["parent"]).lower(),
        ),
    )
    return out


def compute_all() -> dict[str, list[dict]]:
    """Compute parent data for all narratives.

    :return: Dictionary of narrative names and their parent data.
    """
    src = Source()
    out: dict[str, list[dict]] = {}
    for n in load_seeds()["narratives"]:
        name: str = n["name"]
        terms: list[str] = n.get("terms", [])
        allow_name = bool(n.get("allowNameMatch", True))
        block = list(n.get("block", []))
        require_all = bool(n.get("requireAllTerms", False))
        raw = src.parents_for(
            name,
            terms,
            allow_name_match=allow_name,
            block=block,
            require_all_terms=require_all,
        )
        val = _validate_items(raw)
        val = _with_scores(val)[:TOP_N]  # new: add scores + cap
        out[name] = val
    return out


def refresh_all() -> None:
    """Refresh all parent data and persist to storage."""
    generated = compute_all()
    ts = time()
    for k, v in generated.items():
        set_parents(k, v)
        replace_parents(k, v, ts)
