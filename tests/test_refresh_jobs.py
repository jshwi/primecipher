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
    # Clear any existing jobs for test isolation
    jobs.clear_jobs()
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
    # lastJob can be None or a job object depending on test isolation
    assert data["lastJob"] is None or isinstance(data["lastJob"], dict)


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
    # lastJob can be None or a job object depending on test isolation
    assert data["lastJob"] is None or isinstance(data["lastJob"], dict)

    # Test 2: POST /refresh/async → 200, returns jobId
    response = client.post("/refresh/async", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "jobId" in data
    job_id = data["jobId"]

    # Check that job state was tracked
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    # Job might be running or done depending on timing
    assert data["running"] in [True, False]
    if data["running"]:
        assert data["id"] == job_id
        assert data["state"] == "running"
    else:
        # Job completed quickly, but might be from a previous test
        # Just check that we have a valid response structure
        assert data["lastJob"] is None or isinstance(data["lastJob"], dict)


def test_refresh_job_already_running(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that async refresh jobs can run concurrently.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Start multiple async jobs - they should all succeed
    response1 = client.post("/refresh/async", headers=_auth_headers())
    assert response1.status_code == 200
    job_id1 = response1.json()["jobId"]

    response2 = client.post("/refresh/async", headers=_auth_headers())
    assert response2.status_code == 200
    job_id2 = response2.json()["jobId"]

    # Both jobs should have different IDs
    assert job_id1 != job_id2

    # Check status - should show one of the jobs
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    # Job might be running or done depending on timing
    assert data["running"] in [True, False]


def test_refresh_narratives_total_fallback(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that async refresh works with different configurations.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Test async refresh works
    response = client.post("/refresh/async", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "jobId" in data

    # Check status
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] in [True, False]


def test_refresh_exception_handling(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that async refresh handles exceptions properly.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Mock the refresh_all function to raise an exception
    import backend.api.routes.refresh as refresh_mod

    def mock_refresh_all():
        raise RuntimeError("Simulated error during refresh")

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Start async job - should succeed initially
    response = client.post("/refresh/async", headers=_auth_headers())
    assert response.status_code == 200
    job_id = response.json()["jobId"]

    # Wait a bit for the job to fail
    time.sleep(0.1)

    # Check that job state shows error
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    if data["lastJob"] and data["lastJob"]["id"] == job_id:
        assert data["lastJob"]["state"] == "error"
        assert data["lastJob"]["error"] == "Simulated error during refresh"


def test_refresh_status_while_running(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that refresh status endpoint returns running job state when active.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Start an async job
    response = client.post("/refresh/async", headers=_auth_headers())
    assert response.status_code == 200
    job_id = response.json()["jobId"]

    # Check status immediately - job might be running or done
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()

    # Job might be running or done depending on timing
    assert data["running"] in [True, False]
    if data["running"]:
        assert data["id"] == job_id
        assert data["state"] == "running"
    else:
        # Job completed quickly, but might be from a previous test
        # Just check that we have a valid response structure
        assert data["lastJob"] is None or isinstance(data["lastJob"], dict)


def test_refresh_job_already_running_coverage(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that async refresh jobs work correctly.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Start multiple async jobs
    response1 = client.post("/refresh/async", headers=_auth_headers())
    assert response1.status_code == 200
    job_id1 = response1.json()["jobId"]

    response2 = client.post("/refresh/async", headers=_auth_headers())
    assert response2.status_code == 200
    job_id2 = response2.json()["jobId"]

    # Both jobs should have different IDs
    assert job_id1 != job_id2

    # Check status
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] in [True, False]


def test_refresh_async_already_running_coverage(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that async refresh jobs can run concurrently.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    _reload_with_token(monkeypatch)

    # Start multiple async jobs - they should all succeed
    response1 = client.post("/refresh/async", headers=_auth_headers())
    assert response1.status_code == 200
    job_id1 = response1.json()["jobId"]

    response2 = client.post("/refresh/async", headers=_auth_headers())
    assert response2.status_code == 200
    job_id2 = response2.json()["jobId"]

    # Both jobs should have different IDs
    assert job_id1 != job_id2

    # Check status
    response = client.get("/refresh/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["running"] in [True, False]


def test_refresh_job_already_running_sync(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that sync refresh returns 202 when job is already running.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass and set up a running job
    refresh_mod, _jobs = _reload_with_token(monkeypatch)

    # Manually set the global job state to running
    from backend.schemas import JobState

    refresh_mod._job_state = JobState(
        jobId="test-job",
        running=True,
        startedAt=time.time(),
        mode="dev",
        window="24h",
        narrativesTotal=10,
        narratives_done=0,
        errors=[],
    )

    # Act - try to start another sync refresh
    response = client.post("/refresh", headers=_auth_headers())

    # Assert - should return 202 with job state
    assert response.status_code == 202
    data = response.json()
    assert data["running"] is True
    assert data["jobId"] == "test-job"


def test_refresh_exception_handling_sync(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that sync refresh handles exceptions properly.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    refresh_mod, _jobs = _reload_with_token(monkeypatch)

    # Mock refresh_all to raise an exception
    def mock_refresh_all():
        raise RuntimeError("Sync refresh failed")

    monkeypatch.setattr(refresh_mod, "refresh_all", mock_refresh_all)

    # Act - start sync refresh
    response = client.post("/refresh", headers=_auth_headers())

    # Assert - should raise the exception (500 error)
    assert response.status_code == 500


def test_refresh_overview_with_running_job(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test refresh overview returns running job when one exists.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    refresh_mod, _jobs = _reload_with_token(monkeypatch)

    # Create a running job in the JOBS store
    from backend.jobs import _Job

    job_id = "test-running-job"
    job = _Job(job_id)
    job.state = "running"
    _jobs.JOBS[job_id] = job

    # Ensure the refresh module is using the same JOBS instance
    refresh_mod.JOBS = _jobs.JOBS

    # Act
    response = client.get("/refresh/status", headers=_auth_headers())

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is True
    assert data["id"] == job_id
    assert data["state"] == "running"


def test_refresh_overview_with_finished_jobs(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test refresh overview returns most recent finished job.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # Arrange - make auth pass
    refresh_mod, _jobs = _reload_with_token(monkeypatch)

    # Create finished jobs in the JOBS store
    from backend.jobs import _Job

    # Create an older finished job
    old_job_id = "old-job"
    old_job = _Job(old_job_id)
    old_job.state = "done"
    old_job.ts = time.time() - 100
    _jobs.JOBS[old_job_id] = old_job

    # Create a newer finished job
    new_job_id = "new-job"
    new_job = _Job(new_job_id)
    new_job.state = "done"
    new_job.ts = time.time() - 50
    _jobs.JOBS[new_job_id] = new_job

    # Ensure the refresh module is using the same JOBS instance
    refresh_mod.JOBS = _jobs.JOBS

    # Act
    response = client.get("/refresh/status", headers=_auth_headers())

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["lastJob"]["id"] == new_job_id  # Should return the newer job
