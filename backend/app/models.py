from sqlalchemy import Column, Integer, String, Float, Index
from .db import Base

class ParentHit(Base):
    __tablename__ = "parent_hits"
    id = Column(Integer, primary_key=True)
    narrative = Column(String, index=True, nullable=False)
    parent = Column(String, nullable=False)
    matches = Column(Integer, nullable=False)
    ts = Column(Float, nullable=False)  # last refresh timestamp

Index("ix_parenthits_key", ParentHit.narrative, ParentHit.parent, unique=True)
