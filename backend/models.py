"""Database models for the application."""

from sqlalchemy import Column, Float, Index, Integer, String

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
