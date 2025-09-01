"""Pydantic schemas for API requests and responses."""

import typing as t

from pydantic import BaseModel, Field


class Parent(BaseModel):
    """Schema for parent data with matches and optional score."""

    parent: t.Annotated[str, Field(min_length=1)]
    matches: t.Annotated[int, Field(ge=0)]
    score: float | None = None  # present after scoring


class NarrativesResp(BaseModel):
    """Response schema for narratives list."""

    items: list[t.Annotated[str, Field(min_length=1)]]
    lastRefresh: float | None = Field(default=None)


class ParentsResp(BaseModel):
    """Response schema for parents data."""

    narrative: t.Annotated[str, Field(min_length=1)]
    window: t.Annotated[str, Field(min_length=1)]
    items: list[Parent]
    # important: make sure the field exists in the schema so fastapi won't
    # drop it
    nextCursor: str | None = Field(default=None)


class RefreshResp(BaseModel):
    """Response schema for refresh operations."""

    ok: t.Literal[True]
    window: t.Annotated[str, Field(min_length=1)]
    ts: float | None = None
    dryRun: bool | None = None
    items: dict[str, list[Parent]] | None = None


class JobState(BaseModel):
    """Schema for refresh job state."""

    jobId: str
    running: bool
    startedAt: float
    mode: str
    window: str
    narrativesTotal: int
    narratives_done: int
    errors: list[str]
