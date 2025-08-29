from __future__ import annotations
from typing import List, Dict, Protocol

class Adapter(Protocol):
    def parents_for(
        self,
        narrative: str,
        terms: List[str],
        allow_name_match: bool = True,
        block: List[str] | None = None,
        require_all_terms: bool = False,
    ) -> List[Dict]: ...
