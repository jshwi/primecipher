import random
from typing import List, Dict
from .seeds import load_seeds
from .storage import set_parents

def synthesize_parents() -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for n in load_seeds()["narratives"]:
        name = n["name"]
        terms = n["terms"]
        parents = []
        base = random.randint(2, 6)
        for i in range(base):
            t = terms[i % len(terms)] if terms else f"parent{i}"
            parents.append({"parent": f"{t}-source-{i+1}", "matches": random.randint(3, 42)})
        out[name] = sorted(parents, key=lambda x: -x["matches"])
    return out

def refresh_all() -> None:
    # In a real app, query on-chain or APIs here.
    generated = synthesize_parents()
    for k, v in generated.items():
        set_parents(k, v)
