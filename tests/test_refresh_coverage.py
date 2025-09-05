"""Additional tests to improve coverage for refresh.py."""

from unittest.mock import Mock, patch

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
            0,
            "real",
            ["term1"],
        )

        mock_process_real.assert_called_once_with(
            "test_narrative",
            ["term1"],
            "real",
        )
        mock_write.assert_called_once_with("test_narrative", [])


def test_process_dev_mode_job_real_mode_coverage() -> None:
    """Test _process_dev_mode_job real mode to improve coverage."""
    import asyncio

    async def run_test():
        with (
            patch("backend.seeds.load_seeds") as mock_load_seeds,
            patch(
                "backend.api.routes.refresh._process_single_narrative",
            ) as mock_process_single,
        ):

            mock_load_seeds.return_value = {
                "narratives": [{"name": "test", "terms": ["term1"]}],
            }
            mock_process_single.return_value = (True, 1, None)

            await _process_dev_mode_job("test_job", "real", "1h", 1)

            mock_load_seeds.assert_called_once()
            mock_process_single.assert_called_once()

    asyncio.run(run_test())


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
            0,
            "real",
            ["term1"],
            memo,
        )

        # Second call - should use cache (line 161)
        _process_single_narrative(
            "test_narrative",
            "test_job",
            1,
            "real",
            ["term1"],
            memo,
        )

        # Should only call process_real once (first call)
        mock_process_real.assert_called_once_with(
            "test_narrative",
            ["term1"],
            "real",
        )
        # Should call write twice (both calls)
        assert mock_write.call_count == 2


def test_coingecko_adapter_fetch_parents_coverage() -> None:
    """Test CoinGeckoAdapter fetch_parents to improve coverage."""
    from backend.adapters.coingecko import CoinGeckoAdapter

    adapter = CoinGeckoAdapter()
    result = adapter.fetch_parents("test_narrative", ["term1", "term2"])

    assert not result
