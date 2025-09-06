"""Additional tests to improve coverage for refresh.py."""

from unittest.mock import MagicMock, Mock, patch

from backend.adapters import NoopAdapter
from backend.api.routes.refresh import (
    _process_dev_mode_job,
    _process_narrative_real_mode,
    _process_single_narrative,
)


def test_process_narrative_real_mode_coverage() -> None:
    """Test _process_narrative_real_mode to improve coverage."""
    with patch("backend.adapters.get_adapter") as mock_get_adapter:
        mock_adapter = Mock()
        mock_adapter.fetch_parents.return_value = []
        mock_get_adapter.return_value = mock_adapter

        result = _process_narrative_real_mode(
            "test_narrative",
            ["term1", "term2"],
        )

        assert not result
        mock_get_adapter.assert_called_once_with("real")
        mock_adapter.fetch_parents.assert_called_once_with(
            "test_narrative",
            ["term1", "term2"],
        )


def test_process_single_narrative_real_mode_coverage() -> None:
    """Test _process_single_narrative real mode to improve coverage."""
    with (
        patch(
            "backend.api.routes.refresh._process_narrative_real_mode",
        ) as mock_process_real,
        patch(
            "backend.api.routes.refresh._process_narrative_dev_mode",
        ) as mock_process_dev,
        patch(
            "backend.api.routes.refresh._write_narrative_to_storage",
        ) as mock_write,
    ):

        mock_process_real.return_value = []
        mock_process_dev.return_value = []

        _process_single_narrative(
            "test_narrative",
            "test_job",
            mode="real",
            terms=["term1"],
        )

        mock_process_real.assert_called_once_with(
            "test_narrative",
            ["term1"],
            "real",
        )
        mock_write.assert_called_once_with("test_narrative", [])


def test_process_dev_mode_job_real_mode_coverage() -> None:
    """Test _process_dev_mode_job real mode to improve coverage."""
    with (
        patch("backend.seeds.load_seeds") as mock_load_seeds,
        patch(
            "backend.api.routes.refresh._process_single_narrative",
        ) as mock_process_single,
    ):

        mock_load_seeds.return_value = {
            "narratives": [{"name": "test", "terms": ["term1"]}],
        }
        mock_process_single.return_value = (True, None)

        _process_dev_mode_job("test_job", "real", "1h", 1)

        mock_load_seeds.assert_called_once()
        mock_process_single.assert_called_once()


def test_process_dev_mode_job_real_cg_mode_coverage() -> None:
    """Test _process_dev_mode_job real_cg mode to improve coverage."""
    with (
        patch("backend.seeds.load_seeds") as mock_load_seeds,
        patch(
            "backend.api.routes.refresh._process_narrative_real_cg",
        ) as mock_real_cg,
        patch(
            "backend.api.routes.refresh._write_narrative_to_storage",
        ) as mock_write,
        patch(
            "backend.api.routes.refresh._update_job_progress",
        ) as mock_update,
    ):

        mock_load_seeds.return_value = {
            "narratives": [{"name": "test", "terms": ["term1"]}],
        }
        mock_real_cg.return_value = (True, [{"name": "test_item"}])

        _process_dev_mode_job("test_job", "real_cg", "1h", 1)

        mock_load_seeds.assert_called_once()
        mock_real_cg.assert_called_once()
        mock_write.assert_called_once()
        mock_update.assert_called_once()


def test_process_narrative_real_cg_coverage() -> None:
    """Test _process_narrative_real_cg to improve coverage."""
    from backend.api.routes.refresh import _process_narrative_real_cg

    with (
        patch("backend.adapters.get_adapter") as mock_get_adapter,
        patch(
            "backend.api.routes.refresh.current_running_job",
            {"id": "test_job"},
        ),
    ):
        mock_adapter = MagicMock()
        mock_adapter.fetch_parents.return_value = [{"name": "test_item"}]
        mock_get_adapter.return_value = mock_adapter

        # Test with memo cache miss
        should_continue, items = _process_narrative_real_cg(
            "test_narrative",
            ["term1"],
            {},
            "test_job",
        )

        assert should_continue is True
        assert items == [{"name": "test_item"}]
        mock_get_adapter.assert_called_once_with("real_cg")
        mock_adapter.fetch_parents.assert_called_once_with(
            "test_narrative",
            ["term1"],
        )

        # Test with memo cache hit
        memo = {"test_narrative": [{"name": "cached_item"}]}
        should_continue, items = _process_narrative_real_cg(
            "test_narrative",
            ["term1"],
            memo,
            "test_job",
        )

        assert should_continue is True
        assert items == [{"name": "cached_item"}]


def test_create_completed_job_coverage() -> None:
    """Test _create_completed_job to improve coverage."""
    from backend.api.routes.refresh import _create_completed_job

    job = _create_completed_job("test_job", "real_cg", "1h", 10, 5, [])

    assert job["id"] == "test_job"
    assert job["state"] == "done"
    assert job["mode"] == "real_cg"
    assert job["narrativesTotal"] == 10
    assert job["narrativesDone"] == 5
    assert job["calls_used"] == 0  # Counter starts at 0


def test_finalize_job_coverage() -> None:
    """Test _finalize_job to improve coverage."""
    from backend.api.routes.refresh import _finalize_job

    with (
        patch("backend.api.routes.refresh.mark_refreshed") as mock_mark,
        patch("backend.api.routes.refresh.current_running_job", None),
        patch("backend.api.routes.refresh.last_completed_job", None),
        patch("backend.api.routes.refresh.debounce_until", 0),
        patch("backend.api.routes.refresh.last_success_at", 0),
    ):
        _finalize_job("test_job", "real_cg", "1h", 10, 5, [])

        mock_mark.assert_called_once()


def test_process_narrative_real_cg_budget_exceeded_coverage() -> None:
    """Test _process_narrative_real_cg budget exceeded path for coverage."""
    from backend.api.routes.refresh import _process_narrative_real_cg

    # Mock get_cg_calls_count to return high value to trigger budget exceeded
    with patch(
        "backend.api.routes.refresh.get_cg_calls_count",
    ) as mock_get_calls:
        mock_get_calls.return_value = 999999

        should_continue, items = _process_narrative_real_cg(
            "test_narrative",
            ["term1"],
            {},
            "test_job",
        )

        assert should_continue is False
        assert items == []


def test_process_dev_mode_job_real_cg_budget_exceeded_coverage() -> None:
    """Test _process_dev_mode_job real_cg mode budget exceeded for coverage."""
    with (
        patch("backend.seeds.load_seeds") as mock_load_seeds,
        patch(
            "backend.api.routes.refresh._process_narrative_real_cg",
        ) as mock_real_cg,
        patch("backend.api.routes.refresh._finalize_job") as mock_finalize,
    ):

        mock_load_seeds.return_value = {
            "narratives": [{"name": "test", "terms": ["term1"]}],
        }
        # Return budget exceeded
        mock_real_cg.return_value = (False, [])

        _process_dev_mode_job("test_job", "real_cg", "1h", 1)

        mock_load_seeds.assert_called_once()
        mock_real_cg.assert_called_once()
        mock_finalize.assert_called_once()


def test_noop_adapter_fetch_parents_coverage() -> None:
    """Test NoopAdapter.fetch_parents to improve coverage."""
    adapter = NoopAdapter()
    result = adapter.fetch_parents("test_narrative", ["term1", "term2"])
    assert not result


def test_process_single_narrative_memo_cache_coverage() -> None:
    """Test _process_single_narrative memo cache hit to improve coverage."""
    with (
        patch(
            "backend.api.routes.refresh._process_narrative_real_mode",
        ) as mock_process_real,
        patch(
            "backend.api.routes.refresh._write_narrative_to_storage",
        ) as mock_write,
    ):

        mock_process_real.return_value = [{"name": "test", "score": 1.0}]
        memo: dict[str, list[dict]] = {}

        # First call - should process and cache
        _process_single_narrative(
            "test_narrative",
            "test_job",
            mode="real",
            terms=["term1"],
            _memo=memo,
        )

        # Second call - should use cache (line 161)
        _process_single_narrative(
            "test_narrative",
            "test_job",
            mode="real",
            terms=["term1"],
            _memo=memo,
        )

        # Should only call process_real once (first call)
        mock_process_real.assert_called_once_with(
            "test_narrative",
            ["term1"],
            "real",
        )
        # Should call write twice (both calls)
        assert mock_write.call_count == 2


def test_process_narrative_real_ds_mode_coverage() -> None:
    """Test _process_narrative_real_mode with real_ds mode."""
    with patch("backend.adapters.source.parents_for_dexscreener") as mock_ds:
        mock_ds.return_value = [{"parent": "test", "matches": 50}]

        result = _process_narrative_real_mode("test", ["bitcoin"], "real_ds")

        assert result == [{"parent": "test", "matches": 50}]
        mock_ds.assert_called_once_with("test", ["bitcoin"])


def test_coingecko_adapter_fetch_parents_coverage() -> None:
    """Test CoinGeckoAdapter fetch_parents to improve coverage."""
    from backend.adapters.coingecko import CoinGeckoAdapter

    adapter = CoinGeckoAdapter()
    result = adapter.fetch_parents("test_narrative", ["term1", "term2"])

    assert not result


def test_budget_exceeded_max_calls_coverage() -> None:
    """Test budget exceeded max calls for coverage."""
    from backend.api.routes.refresh import _check_budget_limits

    # Mock get_cg_calls_count to return high value
    with patch(
        "backend.api.routes.refresh.get_cg_calls_count",
    ) as mock_get_calls:
        mock_get_calls.return_value = 999999

        # Mock REFRESH_MAX_CALLS to be low
        with patch("backend.api.routes.refresh.REFRESH_MAX_CALLS", 1):
            should_continue, error = _check_budget_limits(
                "test_narrative",
                "real",
            )

            assert not should_continue
            assert error is not None
            assert error["code"] == "BUDGET_EXCEEDED"
            assert error["detail"] == "max calls exceeded"
            assert error["narrative"] == "*"


def test_finalize_job_with_reason_coverage() -> None:
    """Test _finalize_job with reason for coverage."""
    from backend.api.routes.refresh import _finalize_job

    with patch(
        "backend.api.routes.refresh.get_cg_calls_count",
    ) as mock_get_calls:
        mock_get_calls.return_value = 0

        with (
            patch("backend.api.routes.refresh.current_running_job", None),
            patch(
                "backend.api.routes.refresh.last_completed_job",
                None,
            ),
            patch("backend.api.routes.refresh.debounce_until", 0),
            patch(
                "backend.api.routes.refresh.last_success_at",
                0,
            ),
            patch("backend.api.routes.refresh.mark_refreshed") as mock_mark,
        ):
            _finalize_job(
                "test_job",
                "real_cg",
                "1h",
                10,
                5,
                [],
                reason="test_reason",
            )

            # Check that the global variable was set
            from backend.api.routes.refresh import last_completed_job

            assert last_completed_job is not None
            assert last_completed_job["reason"] == "test_reason"
            mock_mark.assert_called_once()


def test_budget_exceeded_finalize_job_coverage() -> None:
    """Test budget exceeded finalize job for coverage."""

    # Mock get_cg_calls_count to return high value
    with patch(
        "backend.api.routes.refresh.get_cg_calls_count",
    ) as mock_get_calls:
        mock_get_calls.return_value = 999999

        # Mock REFRESH_MAX_CALLS to be low
        with (
            patch(
                "backend.api.routes.refresh.REFRESH_MAX_CALLS",
                1,
            ),
            patch(
                "backend.api.routes.refresh.list_narrative_names",
            ) as mock_list,
        ):
            mock_list.return_value = ["narrative1", "narrative2"]

            # Mock the job state
            with patch(
                "backend.api.routes.refresh.current_running_job",
                {
                    "id": "test_job",
                    "state": "running",
                    "ts": 0,
                    "error": None,
                    "jobId": "test_job",
                    "mode": "real",
                    "window": "1h",
                    "narrativesTotal": 2,
                    "narrativesDone": 0,
                    "errors": [],
                    "calls_used": 0,
                },
            ):
                _process_dev_mode_job("test_job", "real", "1h", 2)

                # Check that the job was finalized with budget_exhausted reason
                from backend.api.routes.refresh import last_completed_job

                assert last_completed_job is not None
                assert last_completed_job["reason"] == "budget_exhausted"
