import random
from typing import List, Dict
from .seeds import load_seeds
from .storage import set_parents
from time import time
from .repo import replace_parents
from .adapters.source import Source
from typing import List, Dict
from time import time
from .seeds import load_seeds
from .storage import set_parents
from .repo import replace_parents
from .adapters.source import Source

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

from typing import List, Dict
from time import time
from .seeds import load_seeds
from .storage import set_parents
from .repo import replace_parents
from .adapters.source import Source

def compute_all() -> Dict[str, List[dict]]:
    src = Source()
    out: Dict[str, List[dict]] = {}
    for n in load_seeds()["narratives"]:
        name = n["name"]
        terms = n["terms"]
        v = src.parents_for(name, terms)
        v = sorted(v, key=lambda x: -int(x["matches"]))
        out[name] = v
    return out

def refresh_all() -> None:
    generated = compute_all()
    ts = time()
    for k, v in generated.items():
        set_parents(k, v)
        replace_parents(k, v, ts)
