from typing import List, Dict
from time import time
from .seeds import load_seeds
from .storage import set_parents
from .repo import replace_parents
from .adapters.source import Source
from .schemas import Parent

def _validate_items(items: List[dict]) -> List[dict]:
    # Coerce + validate; raises ValidationError if bad
    return [Parent(**it).model_dump() for it in items]

def compute_all() -> Dict[str, List[dict]]:
    src = Source()
    out: Dict[str, List[dict]] = {}
    for n in load_seeds()["narratives"]:
        name: str = n["name"]
        terms: List[str] = n.get("terms", [])
        allow_name = bool(n.get("allowNameMatch", True))
        block = list(n.get("block", []))
        require_all = bool(n.get("requireAllTerms", False))
        raw = src.parents_for(
            name, terms,
            allow_name_match=allow_name,
            block=block,
            require_all_terms=require_all,
        )
        val = _validate_items(raw)  # <- enforce shape/types
        out[name] = val
    return out

def refresh_all() -> None:
    generated = compute_all()
    ts = time()
    for k, v in generated.items():
        set_parents(k, v)
        replace_parents(k, v, ts)
