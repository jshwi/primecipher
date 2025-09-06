"""Database models for the application."""

from sqlalchemy import Column, Float, Index, Integer, String, UniqueConstraint

from .db import Base


class ParentHit(Base):  # pylint: disable=too-few-public-methods
    """Database model for storing parent hit data."""

    __tablename__ = "parent_hits"
    id = Column(Integer, primary_key=True)
    narrative = Column(String, index=True, nullable=False)
    parent = Column(String, nullable=False)
    matches = Column(Integer, nullable=False)
    ts = Column(Float, nullable=False)  # last refresh timestamp
    # Optional metadata fields
    symbol = Column(String, nullable=True)
    source = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    marketCap = Column(Float, nullable=True)
    vol24h = Column(Float, nullable=True)
    image = Column(String, nullable=True)
    url = Column(String, nullable=True)


Index("ix_parenthits_key", ParentHit.narrative, ParentHit.parent, unique=True)


class ParentMeta(Base):  # pylint: disable=too-few-public-methods
    """Database model for storing parent metadata."""

    __tablename__ = "parent_meta"
    id = Column(Integer, primary_key=True)
    narrative = Column(String, nullable=False)
    parent = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    vol24h = Column(Float, nullable=True)
    liquidity_usd = Column(Float, nullable=True)
    chain = Column(String, nullable=True)
    address = Column(String, nullable=True)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    updated_at = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "narrative",
            "parent",
            name="uq_parent_meta_narrative_parent",
        ),
    )
