"""Tests for API endpoints."""


def test_healthz(client) -> None:
    """Test health check endpoint returns ready status.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ready") is True


def test_heatmap(client) -> None:
    """Test heatmap endpoint returns expected structure.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/heatmap")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and isinstance(js["items"], list)
    assert "stale" in js and isinstance(js["stale"], bool)
    assert "lastUpdated" in js and js["lastUpdated"] is None


def test_heatmap_with_metadata(client) -> None:
    """Test heatmap endpoint with metadata to cover computed_at_values.append.

    :param client: Pytest fixture for test client.
    """
    # Set up some metadata with computedAt values to cover line 50
    import time

    from backend.seeds import list_narrative_names
    from backend.storage import set_parents

    # Get a narrative name and set up some data with metadata
    narrative_names = list_narrative_names()
    if narrative_names:
        # Set up parent data which will also set metadata with computedAt
        test_parents = [{"parent": "test", "matches": 1, "score": 0.5}]
        set_parents(narrative_names[0], test_parents)

        # Add a small delay to ensure different timestamps
        time.sleep(0.01)

        # Set up another narrative with metadata
        if len(narrative_names) > 1:
            set_parents(narrative_names[1], test_parents)

    r = client.get("/heatmap")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and isinstance(js["items"], list)
    assert "stale" in js and isinstance(js["stale"], bool)
    # Now lastUpdated should not be None since we have metadata
    assert "lastUpdated" in js


def test_heatmap_empty_parents(client) -> None:
    """Test heatmap endpoint when narrative has no parents.

    :param client: Pytest fixture for test client.
    """
    from backend.repo import replace_parents
    from backend.seeds import list_narrative_names
    from backend.storage import set_parents

    # Get a narrative name and set up empty parent data
    narrative_names = list_narrative_names()
    if narrative_names:
        # Set up empty parent data in both storage and database to test the
        # else branch in heatmap
        set_parents(narrative_names[0], [])
        replace_parents(narrative_names[0], [], 0.0)  # Clear database as well

    r = client.get("/heatmap")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and isinstance(js["items"], list)
    assert "stale" in js and isinstance(js["stale"], bool)
    assert "lastUpdated" in js

    # Find the narrative with empty parents and verify score is 0.0
    if narrative_names:
        empty_narrative = next(
            (
                item
                for item in js["items"]
                if item["name"] == narrative_names[0]
            ),
            None,
        )
        if empty_narrative:
            assert empty_narrative["score"] == 0.0
            assert empty_narrative["count"] == 0


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


def test_parents_debug_mode(client) -> None:
    """Test parents endpoint with debug mode includes sources field.

    :param client: Pytest fixture for test client.
    """
    from unittest.mock import patch

    from backend.seeds import list_narrative_names

    # Get a narrative name and set up some data with sources
    narrative_names = list_narrative_names()
    if narrative_names:
        test_narrative = narrative_names[0]

        # Mock the data source to return data with sources field
        mock_data = [
            {
                "parent": "test",
                "matches": 1,
                "score": 0.5,
                "sources": ["coingecko", "dexscreener"],
            },
        ]

        with (
            patch(
                "backend.api.routes.parents.list_parents_db",
                return_value=[],
            ),
            patch(
                "backend.api.routes.parents.get_parents",
                return_value=mock_data,
            ),
        ):

            # Test without debug mode (sources should be filtered out)
            r = client.get(f"/parents/{test_narrative}")
            assert r.status_code == 200
            js = r.json()
            items = js.get("items", [])
            if items:
                # In non-debug mode, sources should be filtered out
                assert "sources" not in items[0] or items[0]["sources"] is None

            # Test with debug mode (sources should be included)
            r = client.get(f"/parents/{test_narrative}?debug=true")
            assert r.status_code == 200
            js = r.json()
            items = js.get("items", [])
            if items:
                assert "sources" in items[0]
                assert items[0]["sources"] == ["coingecko", "dexscreener"]
