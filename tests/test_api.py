"""Tests for API endpoints."""


def test_healthz(client) -> None:
    """Test health check endpoint returns ready status.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ready") is True


def test_narratives_list(client) -> None:
    """Test narratives list endpoint returns items list.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/narratives")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and isinstance(js["items"], list)


def test_narratives_list_with_job_errors(client) -> None:
    """Test narratives list endpoint when last job had errors.

    :param client: Pytest fixture for test client.
    """
    # Mock the last_completed_job to have errors
    from backend.api.routes import refresh
    from backend.api.routes.narratives import _get_last_job_errors

    # Save original value
    original_job = refresh.last_completed_job

    # Set a job with errors
    refresh.last_completed_job = {
        "id": "test-job",
        "state": "done",
        "errors": ["error1", "error2"],
    }

    try:
        # Test the function directly to ensure coverage
        error_count = _get_last_job_errors()
        assert error_count == 2

        # Test the endpoint
        r = client.get("/narratives")
        assert r.status_code == 200
        js = r.json()
        assert "items" in js and isinstance(js["items"], list)
        # Should be stale due to job errors
        assert js.get("stale") is True
    finally:
        # Restore original value
        refresh.last_completed_job = original_job


def test_parents_404_unknown(client) -> None:
    """Test parents endpoint returns 404 for unknown narrative.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/parents/__nope__")
    assert r.status_code == 404


def test_refresh_then_parents_flow(client) -> None:
    """Test complete refresh and parents flow.

    :param client: Pytest fixture for test client.
    """
    r = client.post("/refresh")
    assert r.status_code == 200 and "jobId" in r.json()

    from backend.seeds import list_narrative_names

    for n in list_narrative_names():  # no hardcoded 'moodeng'
        r2 = client.get(f"/parents/{n}")
        assert r2.status_code == 200
        items = r2.json().get("items")
        assert isinstance(items, list) and len(items) > 0
        for it in items:
            assert "parent" in it and "matches" in it and "score" in it
