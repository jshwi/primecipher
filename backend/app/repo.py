"""Database repository operations for parent data."""

from sqlalchemy import delete, select

from .db import Base, SessionLocal, engine
from .models import ParentHit


def init_db() -> None:
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def replace_parents(narrative: str, items: list[dict], ts: float) -> None:
    """Replace all parent data for a narrative with new items.

    :param narrative: The narrative to replace parent data for.
    :param items: The new parent data to replace with.
    :param ts: The timestamp of the replacement.
    """
    with SessionLocal() as s:
        s.execute(delete(ParentHit).where(ParentHit.narrative == narrative))
        for it in items:
            s.add(
                ParentHit(
                    narrative=narrative,
                    parent=it["parent"],
                    matches=int(it["matches"]),
                    ts=ts,
                ),
            )
        s.commit()


def list_parents(narrative: str) -> list[dict]:
    """List all parent data for a narrative, ordered by matches descending.

    :param narrative: The narrative to list parent data for.
    :return: List of parent data for the narrative.
    """
    with SessionLocal() as s:
        rows = (
            s.execute(
                select(ParentHit)
                .where(ParentHit.narrative == narrative)
                .order_by(ParentHit.matches.desc()),
            )
            .scalars()
            .all()
        )
        return [{"parent": r.parent, "matches": r.matches} for r in rows]
