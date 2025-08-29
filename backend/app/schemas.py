from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, conint, constr

class Parent(BaseModel):
    parent: constr(min_length=1)
    matches: conint(ge=0)
    score: Optional[float] = None  # present after scoring

class NarrativesResp(BaseModel):
    items: List[constr(min_length=1)]
    lastRefresh: Optional[float] = Field(default=None)

class ParentsResp(BaseModel):
    narrative: constr(min_length=1)
    window: constr(min_length=1)
    items: List[Parent]
    # IMPORTANT: make sure the field exists in the schema so FastAPI won't drop it
    nextCursor: Optional[str] = Field(default=None)

class RefreshResp(BaseModel):
    ok: Literal[True]
    window: constr(min_length=1)
    ts: Optional[float] = None
    dryRun: Optional[bool] = None
    items: Optional[Dict[str, List[Parent]]] = None

from pydantic import BaseModel, Field
from typing import List, Dict

class SeedTerms(BaseModel):
    include: List[str] = Field(default_factory=list)
    require_all: bool = False
    synonyms: Dict[str, List[str]] = Field(default_factory=dict)

class SeedBranch(BaseModel):
    key: str
    include: List[str] = Field(default_factory=list)
    block: List[str] = Field(default_factory=list)
    weight: float = 1.0
    require_all: bool = False

class SeedNarrative(BaseModel):
    name: str
    terms: SeedTerms
    block: List[str] = Field(default_factory=list)
    weight: float = 1.0
    branches: List[SeedBranch] = Field(default_factory=list)

class SeedsV2(BaseModel):
    version: int = 2
    narratives: List[SeedNarrative]
