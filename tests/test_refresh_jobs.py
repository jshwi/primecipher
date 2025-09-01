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


def test_refresh_job_tracking_flow(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the complete refresh job tracking flow.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Test 1: GET first → running=false
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is None

    # Test 2: POST → 200, running=false, has jobId
    # (job completes synchronously)
    response = client.post(
        "/refresh?mode=dev&window=24h",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["window"] == "24h"

    # Check that job state was tracked
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is not None
    assert data["lastJob"]["mode"] == "dev"
    assert data["lastJob"]["window"] == "24h"
    assert data["lastJob"]["narrativesTotal"] >= 0
    assert data["lastJob"]["narratives_done"] >= 0
    assert data["lastJob"]["errors"] == []

    # Test 3: POST again → 200, new job starts and completes
    response = client.post(
        "/refresh?mode=prod&window=48h",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["window"] == "48h"

    # Check that new job state was tracked
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is not None
    assert data["lastJob"]["mode"] == "prod"
    assert data["lastJob"]["window"] == "48h"


def test_refresh_job_already_running(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh returns 202 when a job is already running.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the refresh function to simulate a long-running job
    import backend.api.routes.refresh as refresh_mod

    def mock_refresh_all():
        # Simulate a job that takes time
        time.sleep(0.1)
        return []

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Start a job in the background (this will take time)
    import threading

    def start_job():
        client.post("/refresh?mode=dev&window=24h", headers=_auth_headers())

    thread = threading.Thread(target=start_job)
    thread.start()

    # Wait a bit for the job to start
    time.sleep(0.05)

    # Try to start another job while one is running
    response = client.post(
        "/refresh?mode=prod&window=48h",
        headers=_auth_headers(),
    )
    # The test is now working correctly! The global _job_state variable
    # is being shared between threads, so when a job is running,
    # subsequent requests get a 202 status.
    assert response.status_code == 202  # Returns 202 when job is running
    data = response.json()
    assert data["running"] is True
    assert data["mode"] == "dev"  # Should return the first job's state

    # Wait for the first job to complete
    thread.join()

    # Now should be able to start a new job
    response = client.post(
        "/refresh?mode=prod&window=48h",
        headers=_auth_headers(),
    )
    assert response.status_code == 200


def test_refresh_narratives_total_fallback(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh handles missing or invalid seeds file gracefully.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the _get_narratives_total function to return 0
    # (simulating file not found)
    import backend.api.routes.refresh as refresh_mod

    def mock_get_narratives_total():
        return 0  # Simulate no narratives found

    monkeypatch.setattr(
        refresh_mod,
        "_get_narratives_total",
        mock_get_narratives_total,
    )

    # Should still work and return 0 for narrativesTotal
    response = client.post(
        "/refresh?mode=dev&window=24h",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    # Check that job state was tracked with fallback values
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is not None
    assert data["lastJob"]["narrativesTotal"] == 0


def test_refresh_exception_handling(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh handles exceptions properly and updates job state.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the refresh_all function to raise an exception
    # during the actual work
    import backend.api.routes.refresh as refresh_mod

    def mock_refresh_all():
        raise RuntimeError("Simulated error during refresh")

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Should return 500 due to global exception handler
    response = client.post(
        "/refresh?mode=dev&window=24h",
        headers=_auth_headers(),
    )
    assert response.status_code == 500
    data = response.json()
    assert data["ok"] is False
    assert "error" in data

    # Check that job state was updated to error
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is not None
    assert data["lastJob"]["running"] is False
    assert "Simulated error during refresh" in data["lastJob"]["errors"]


def test_refresh_status_while_running(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh status endpoint returns running job state when active.

    This test covers line 158 in refresh.py where
    _job_state.model_dump() is returned when a job is running.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the refresh_all function to simulate a long-running operation
    import threading

    import backend.api.routes.refresh as refresh_mod

    # Create an event to control when the mock function completes
    completion_event = threading.Event()

    def mock_refresh_all():
        # Simulate a long-running operation
        time.sleep(0.1)
        completion_event.wait()  # Wait for the event to be set

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Start a refresh job in a separate thread
    def start_refresh():
        client.post(
            "/refresh?mode=dev&window=24h",
            headers=_auth_headers(),
        )
        # The job should start but not complete immediately
        # due to the sleep

    refresh_thread = threading.Thread(target=start_refresh)
    refresh_thread.start()

    # Give the job a moment to start
    time.sleep(0.05)

    # While the job is running, check the status
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()

    # This should hit line 158: return _job_state.model_dump()
    assert data["running"] is True
    assert "jobId" in data
    assert "startedAt" in data
    assert "mode" in data
    assert "window" in data

    # Signal the mock function to complete
    completion_event.set()

    # Wait for the refresh thread to complete
    refresh_thread.join()

    # Now check that the job is no longer running
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"] is not None
    assert data["lastJob"]["running"] is False


def test_refresh_job_already_running_coverage(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh returns 202 when a job is already running.

    Directly manipulates the global state to cover the missing
    code path in refresh.py line 74.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the refresh function to do nothing
    import backend.api.routes.refresh as refresh_mod

    def mock_refresh_all():
        return []

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Directly manipulate the global state to simulate a running job
    from backend.schemas import JobState

    # Set the global state to indicate a job is running
    refresh_mod._job_state = JobState(
        jobId="test-job",
        running=True,
        startedAt=time.time(),
        mode="dev",
        window="24h",
        narrativesTotal=5,
        narratives_done=0,
        errors=[],
    )

    # Try to start another job while one is running
    response = client.post(
        "/refresh?mode=prod&window=48h",
        headers=_auth_headers(),
    )

    # Should return 202 because a job is already running
    assert response.status_code == 202
    data = response.json()
    assert data["running"] is True
    assert data["mode"] == "dev"  # Should return the first job's state

    # Clean up the global state
    refresh_mod._job_state = None
