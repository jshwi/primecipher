"""Background job management for refresh operations."""

import asyncio
import time
import typing as t
import uuid

State = t.Literal["queued", "running", "done", "error"]


class _Job:  # pylint: disable=too-few-public-methods
    """Internal job representation."""

    __slots__ = ("id", "state", "ts", "error")

    def __init__(self, jid: str):
        self.id = jid
        self.state: State = "queued"
        self.ts: float = time.time()
        self.error: str | None = None


JOBS: dict[str, _Job] = {}
_LOCK = asyncio.Lock()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


async def _run_refresh(refresh_fn):
    await refresh_fn()


async def start_refresh_job(refresh_fn) -> str:
    """Schedule refresh_fn() to run in the background.

    Returns a short job id immediately.

    :param refresh_fn: The function to run in the background.
    :return: A short job id.
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
        except (
            RuntimeError,
            ValueError,
            OSError,
        ) as e:  # more specific exceptions
            job.state = "error"
            job.error = str(e)
        finally:
            job.ts = time.time()

    # fire-and-forget (keep reference so it isn't gc'd)
    asyncio.create_task(_runner())
    return jid


def get_job(jid: str) -> dict | None:
    """Get job information by ID.

    :param jid: The ID of the job to get information for.
    :return: Job information.
    """
    job = JOBS.get(jid)
    if not job:
        return None
    return {"id": job.id, "state": job.state, "ts": job.ts, "error": job.error}


def gc_jobs(max_age_sec: int = 3600) -> None:
    """Drop completed/error jobs older than max_age_sec.

    :param max_age_sec: The maximum age of a job in seconds.
    """
    now = time.time()
    to_drop = [
        k
        for k, j in JOBS.items()
        if j.state in ("done", "error") and now - j.ts > max_age_sec
    ]
    for k in to_drop:
        JOBS.pop(k, None)
