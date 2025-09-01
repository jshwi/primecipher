"""Tests for refresh jobs functionality."""

import asyncio
import importlib
import time
import typing as t

import pytest


def _auth_headers(token: str = "testtoken") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _reload_with_token(
    monkeypatch: pytest.MonkeyPatch,
    token: str = "testtoken",
) -> tuple[t.Any, t.Any]:
    # Ensure the auth layer expects our token
    monkeypatch.setenv("REFRESH_TOKEN", token)
    # Reload modules that read env at import time
    from backend.deps import auth

    importlib.reload(auth)
    import backend.api.routes.refresh as rj

    importlib.reload(rj)
    from backend import jobs

    importlib.reload(jobs)
    return rj, jobs


def _spin_until(
    cond: t.Callable[[], bool],
    timeout: float = 1.0,
    step: float = 0.01,
) -> bool:
    # Spin-wait helper for state transitions in background task
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(step)
    return False


def test_refresh_async_and_status_done(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test async refresh job completes successfully.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange
    jobs = _reload_with_token(monkeypatch)[1]

    # Make the background job fast & deterministic
    # Patch the _run_refresh to tick the state machine without doing any
    # real work
    async def _noop() -> None:
        await asyncio.sleep(0)

    monkeypatch.setattr(jobs, "_run_refresh", lambda _: _noop())

    # Act: start job
    resp = client.post("/refresh/async", headers=_auth_headers())
    assert resp.status_code == 200
    job_id = resp.json()["jobId"]

    # Assert: it moves to done
    def _is_done() -> bool:
        s = client.get(f"/refresh/status/{job_id}", headers=_auth_headers())
        assert s.status_code == 200
        state = s.json()["state"]
        # state should progress through queued|running to done quickly
        return state == "done"

    assert _spin_until(
        _is_done,
        timeout=1.0,
    ), "job did not reach 'done' state in time"


def test_refresh_async_error_and_status(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test async refresh job handles errors properly.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange
    jobs = _reload_with_token(monkeypatch)[1]

    # Force background job to raise
    async def _boom() -> None:
        raise RuntimeError("kaboom")

    monkeypatch.setattr(jobs, "_run_refresh", lambda _: _boom())

    # Act: start job
    resp = client.post("/refresh/async", headers=_auth_headers())
    assert resp.status_code == 200
    job_id = resp.json()["jobId"]

    # Assert: it ends in error and exposes message
    def _is_error() -> bool:
        s = client.get(f"/refresh/status/{job_id}", headers=_auth_headers())
        assert s.status_code == 200
        js = s.json()
        return js["state"] == "error" and ("kaboom" in (js.get("error") or ""))

    assert _spin_until(
        _is_error,
        timeout=1.0,
    ), "job did not reach 'error' state in time"

    # Unknown job id → 404
    s404 = client.get("/refresh/status/doesnotexist", headers=_auth_headers())
    assert s404.status_code == 404


def test_jobs_gc_removes_old_done() -> None:
    """Test that garbage collection removes old completed jobs."""
    # Work directly with the jobs module to hit GC branches
    from backend import jobs

    importlib.reload(jobs)

    # Create a job and mark it as done immediately by running a no-op
    async def _noop() -> None:
        return

    jid = asyncio.run(jobs.start_refresh_job(_noop))

    # Wait until job transitions to done
    def _done() -> bool:
        j = jobs.get_job(jid)
        return j is not None and j["state"] == "done"

    assert _spin_until(_done, timeout=1.0)

    # Age it and GC
    # Make it look old by mutating internal ts
    jobs.JOBS[jid].ts -= 9999  # type: ignore[attr-defined]
    jobs.gc_jobs(max_age_sec=1)

    # It should be gone
    assert jobs.get_job(jid) is None


# append to backend/tests/test_refresh.py


def test_refresh_async_executes_do_calls(
    monkeypatch: pytest.MonkeyPatch,
    client: t.Any,
) -> None:
    """Test that async refresh executes the required function calls.

    :param monkeypatch: Pytest fixture for patching.
    :param client: Pytest fixture for test client.
    """
    # make auth pass and reload the route module so we can patch its
    # locals
    monkeypatch.setenv("REFRESH_TOKEN", "testtoken")
    import backend.api.routes.refresh as rj

    importlib.reload(rj)

    # Count calls to the inner functions invoked by _do()
    counters = {"refresh": 0, "mark": 0}

    def fake_refresh_all() -> None:
        counters["refresh"] += 1

    def fake_mark_refreshed() -> None:
        counters["mark"] += 1

    # Patch the functions that _do() calls (lines 16–17)
    monkeypatch.setattr(rj, "refresh_all", fake_refresh_all, raising=True)
    monkeypatch.setattr(
        rj,
        "mark_refreshed",
        fake_mark_refreshed,
        raising=True,
    )

    # Kick off the async job (do NOT patch jobs._run_refresh here)
    resp = client.post(
        "/refresh/async",
        headers={"Authorization": "Bearer testtoken"},
    )
    assert resp.status_code == 200
    jid = resp.json()["jobId"]

    deadline = time.time() + 1.0
    while time.time() < deadline:
        s = client.get(
            f"/refresh/status/{jid}",
            headers={"Authorization": "Bearer testtoken"},
        )
        assert s.status_code == 200
        if s.json()["state"] == "done":
            break
        time.sleep(0.01)
    else:
        raise AssertionError("job did not reach 'done' state in time")

    # Both inner calls were executed by _do()
    assert counters["refresh"] == 1
    assert counters["mark"] == 1


def test_refresh_overview_status(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the refresh overview endpoint returns expected status.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Act
    response = client.get("/refresh/status", headers=_auth_headers())

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "lastJob" in data
    assert data["running"] is False
    assert data["lastJob"] is None
