"""Pydantic schemas for API requests and responses."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Parent(BaseModel):
    """Schema for parent data with matches and optional score."""

    parent: Annotated[str, Field(min_length=1)]
    matches: Annotated[int, Field(ge=0)]
    score: float | None = None  # present after scoring


class NarrativesResp(BaseModel):
    """Response schema for narratives list."""

    items: list[Annotated[str, Field(min_length=1)]]
    lastRefresh: float | None = Field(default=None)


class ParentsResp(BaseModel):
    """Response schema for parents data."""

    narrative: Annotated[str, Field(min_length=1)]
    window: Annotated[str, Field(min_length=1)]
    items: list[Parent]
    # important: make sure the field exists in the schema so fastapi won't
    # drop it
    nextCursor: str | None = Field(default=None)


class RefreshResp(BaseModel):
    """Response schema for refresh operations."""

    ok: Literal[True]
    window: Annotated[str, Field(min_length=1)]
    ts: float | None = None
    dryRun: bool | None = None
    items: dict[str, list[Parent]] | None = None
