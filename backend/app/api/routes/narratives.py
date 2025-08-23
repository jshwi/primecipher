# backend/app/api/routes/narratives.py
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

# Use relative import so this works regardless of PYTHONPATH/CWD
from ...seeds import load_narrative_seeds

router = APIRouter(prefix="", tags=["narratives"])


@router.get("/narratives")
def list_narratives() -> Dict[str, Any]:
    """
    Returns available narratives from seeds, with parent symbols.
    Example:
    {
      "narratives": [
        {"key": "dogs", "parents": ["WIF","MOODENG"], "num_parents": 2},
        {"key": "ai",   "parents": ["..."],           "num_parents": 1}
      ]
    }
    """
    seeds = load_narrative_seeds()
    out: List[Dict[str, Any]] = []
    for s in seeds:
        key = s.get("narrative")
        parents: List[str] = []
        for p in (s.get("parents") or []):
            sym = (p.get("symbol") or "").upper()
            if sym:
                parents.append(sym)
        out.append({"key": key, "parents": parents, "num_parents": len(parents)})
    out.sort(key=lambda x: (x["key"] or ""))
    return {"narratives": out}

