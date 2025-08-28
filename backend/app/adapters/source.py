import os
from typing import List, Dict

MODE = (os.getenv("SOURCE_MODE") or "dev").lower()

def _deterministic_items(narrative: str, terms: List[str]) -> List[Dict]:
    # Always 3 items, stable ordering, stable counts
    base_terms = terms or [narrative, "parent", "seed"]
    parents = [
        {"parent": f"{base_terms[0]}-source-1", "matches": 11},
        {"parent": f"{base_terms[min(1, len(base_terms)-1)]}-source-2", "matches": 10},
        {"parent": f"{base_terms[min(2, len(base_terms)-1)]}-source-3", "matches": 9},
    ]
    return parents

def _random_items(terms: List[str]) -> List[Dict]:
    import random
    n = random.randint(2, 6)
    out = []
    for i in range(n):
        t = terms[i % len(terms)] if terms else f"parent{i}"
        out.append({"parent": f"{t}-source-{i+1}", "matches": random.randint(3, 42)})
    out.sort(key=lambda x: -x["matches"])
    return out

class Source:
    def parents_for(self, narrative: str, terms: List[str]) -> List[Dict]:
        if MODE in {"test", "ci"}:
            return _deterministic_items(narrative, terms)
        return _random_items(terms)
