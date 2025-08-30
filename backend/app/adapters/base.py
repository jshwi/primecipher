from __future__ import annotations

from typing import Protocol


class Adapter(Protocol):
    def parents_for(
        self,
        narrative: str,
        terms: list[str],
        allow_name_match: bool = True,
        block: list[str] | None = None,
        require_all_terms: bool = False,
    ) -> list[dict]: ...
