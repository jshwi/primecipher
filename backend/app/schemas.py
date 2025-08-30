from typing import Literal, Optional

from pydantic import BaseModel, Field, conint, constr


class Parent(BaseModel):
    parent: constr(min_length=1)
    matches: conint(ge=0)
    score: float | None = None  # present after scoring


class NarrativesResp(BaseModel):
    items: list[constr(min_length=1)]
    lastRefresh: float | None = Field(default=None)


class ParentsResp(BaseModel):
    narrative: constr(min_length=1)
    window: constr(min_length=1)
    items: list[Parent]
    # IMPORTANT: make sure the field exists in the schema so FastAPI won't drop it
    nextCursor: str | None = Field(default=None)


class RefreshResp(BaseModel):
    ok: Literal[True]
    window: constr(min_length=1)
    ts: float | None = None
    dryRun: bool | None = None
    items: dict[str, list[Parent]] | None = None
