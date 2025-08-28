from typing import List, Dict
import random

class Source:
    def parents_for(self, narrative: str, terms: List[str]) -> List[Dict]:
        base = random.randint(2, 6)
        out = []
        for i in range(base):
            t = terms[i % len(terms)] if terms else f"parent{i}"
            out.append({"parent": f"{t}-source-{i+1}", "matches": random.randint(3, 42)})
        return out
