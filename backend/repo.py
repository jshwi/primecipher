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
    # Deduplicate items within the same narrative
    seen = set()
    filtered_items = []
    for it in items:
        k = (narrative, (it.get("parent") or "").strip().lower())
        if k in seen:
            continue
        seen.add(k)
        filtered_items.append(it)

    with SessionLocal() as s:
        s.execute(delete(ParentHit).where(ParentHit.narrative == narrative))
        for it in filtered_items:
            s.add(
                ParentHit(
                    narrative=narrative,
                    parent=it["parent"],
                    matches=int(it["matches"]),
                    ts=ts,
                    symbol=it.get("symbol"),
                    source=it.get("source"),
                    price=it.get("price"),
                    marketCap=it.get("marketCap"),
                    vol24h=it.get("vol24h"),
                    image=it.get("image"),
                    url=it.get("url"),
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
        return [
            {
                "parent": r.parent,
                "matches": r.matches,
                "symbol": r.symbol,
                "source": r.source,
                "price": r.price,
                "marketCap": r.marketCap,
                "vol24h": r.vol24h,
                "image": r.image,
                "url": r.url,
            }
            for r in rows
        ]
