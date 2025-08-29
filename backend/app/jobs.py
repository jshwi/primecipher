import asyncio
import time
import uuid
from typing import Dict, Literal, Optional

State = Literal["queued", "running", "done", "error"]

class _Job:
    __slots__ = ("id", "state", "ts", "error")
    def __init__(self, jid: str):
        self.id = jid
        self.state: State = "queued"
        self.ts: float = time.time()
        self.error: Optional[str] = None

JOBS: Dict[str, _Job] = {}
_LOCK = asyncio.Lock()

def _new_id() -> str:
    return uuid.uuid4().hex[:12]

async def _run_refresh(refresh_fn):
    await refresh_fn()

async def start_refresh_job(refresh_fn) -> str:
    """
    Schedule refresh_fn() to run in the background.
    Returns a short job id immediately.
    """
    jid = _new_id()
    job = _Job(jid)
    async with _LOCK:
        JOBS[jid] = job

    async def _runner():
        job.state = "running"
        job.ts = time.time()
        try:
            await _run_refresh(refresh_fn)
            job.state = "done"
        except Exception as e:  # noqa: BLE001 (we want to trap anything)
            job.state = "error"
            job.error = str(e)
        finally:
            job.ts = time.time()

    # fire-and-forget (keep reference so it isn't GC'd)
    asyncio.create_task(_runner())
    return jid

def get_job(jid: str) -> Optional[dict]:
    job = JOBS.get(jid)
    if not job:
        return None
    return {"id": job.id, "state": job.state, "ts": job.ts, "error": job.error}

def gc_jobs(max_age_sec: int = 3600) -> None:
    """Drop completed/error jobs older than max_age_sec."""
    now = time.time()
    to_drop = [k for k, j in JOBS.items() if j.state in ("done", "error") and now - j.ts > max_age_sec]
    for k in to_drop:
        JOBS.pop(k, None)
