"""Database repository operations for parent data."""

from sqlalchemy import delete, select, text

from .db import Base, SessionLocal, engine
from .models import ParentHit, ParentMeta


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
        # Delete existing hits for this narrative
        s.execute(delete(ParentHit).where(ParentHit.narrative == narrative))

        # Insert new hits and UPSERT metadata
        for it in filtered_items:
            # Insert hit data
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

            # UPSERT metadata into parent_meta table
            s.execute(
                text(
                    """
                    INSERT INTO parent_meta
                    (narrative, parent, symbol, price, market_cap, vol24h,
                    liquidity_usd, chain, address, url, source, updated_at)
                    VALUES (:narrative, :parent, :symbol, :price, :market_cap,
                            :vol24h, :liquidity_usd, :chain, :address, :url,
                            :source, :updated_at)
                    ON CONFLICT(narrative, parent)
                    DO UPDATE SET
                        symbol = EXCLUDED.symbol,
                        price = EXCLUDED.price,
                        market_cap = EXCLUDED.market_cap,
                        vol24h = EXCLUDED.vol24h,
                        liquidity_usd = EXCLUDED.liquidity_usd,
                        chain = EXCLUDED.chain,
                        address = EXCLUDED.address,
                        url = EXCLUDED.url,
                        source = EXCLUDED.source,
                        updated_at = EXCLUDED.updated_at
                """,
                ),
                {
                    "narrative": narrative,
                    "parent": it["parent"],
                    "symbol": it.get("symbol"),
                    "price": it.get("price"),
                    "market_cap": it.get("marketCap"),
                    "vol24h": it.get("vol24h"),
                    "liquidity_usd": it.get("liquidityUsd"),
                    "chain": it.get("chain"),
                    "address": it.get("address"),
                    "url": it.get("url"),
                    "source": it.get("source"),
                    "updated_at": ts,
                },
            )
        s.commit()


def list_parents(narrative: str) -> list[dict]:
    """List all parent data for a narrative, ordered by matches descending.

    :param narrative: The narrative to list parent data for.
    :return: List of parent data for the narrative.
    """
    with SessionLocal() as s:
        # JOIN parent_hits with parent_meta to get enriched data
        rows = s.execute(
            select(
                ParentHit.parent,
                ParentHit.matches,
                ParentHit.symbol,
                ParentHit.source,
                ParentHit.price,
                ParentHit.marketCap,
                ParentHit.vol24h,
                ParentHit.image,
                ParentHit.url,
                ParentMeta.symbol.label("meta_symbol"),
                ParentMeta.price.label("meta_price"),
                ParentMeta.market_cap.label("meta_market_cap"),
                ParentMeta.vol24h.label("meta_vol24h"),
                ParentMeta.liquidity_usd,
                ParentMeta.chain,
                ParentMeta.address,
                ParentMeta.url.label("meta_url"),
                ParentMeta.source.label("meta_source"),
            )
            .select_from(ParentHit)
            .outerjoin(
                ParentMeta,
                (ParentHit.narrative == ParentMeta.narrative)
                & (ParentHit.parent == ParentMeta.parent),
            )
            .where(ParentHit.narrative == narrative)
            .order_by(ParentHit.matches.desc()),
        ).all()
        return [
            {
                "parent": r.parent,
                "matches": r.matches,
                "symbol": r.meta_symbol or r.symbol,
                "source": r.meta_source or r.source,
                "price": r.meta_price or r.price,
                "marketCap": r.meta_market_cap or r.marketCap,
                "vol24h": r.meta_vol24h or r.vol24h,
                "liquidityUsd": r.liquidity_usd,
                "chain": r.chain,
                "address": r.address,
                "url": r.meta_url or r.url,
                "image": r.image,
            }
            for r in rows
        ]
