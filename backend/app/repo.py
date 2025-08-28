from typing import List, Dict
from sqlalchemy import select, delete
from .db import SessionLocal, Base, engine
from .models import ParentHit

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def replace_parents(narrative: str, items: List[dict], ts: float) -> None:
    with SessionLocal() as s:
        s.execute(delete(ParentHit).where(ParentHit.narrative == narrative))
        for it in items:
            s.add(ParentHit(narrative=narrative, parent=it["parent"], matches=int(it["matches"]), ts=ts))
        s.commit()

def list_parents(narrative: str) -> List[Dict]:
    with SessionLocal() as s:
        rows = s.execute(select(ParentHit).where(ParentHit.narrative == narrative).order_by(ParentHit.matches.desc())).scalars().all()
        return [{"parent": r.parent, "matches": r.matches} for r in rows]
