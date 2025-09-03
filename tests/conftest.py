"""Pytest configuration and fixtures."""

import os
import sys
import typing as t
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# set env before importing app modules
here = Path(__file__).parent
repo_root = (here / "..").resolve()
os.environ.setdefault(
    "SOURCE_MODE",
    "test",
)  # deterministic adapter mode for tests

# now import app after env is set
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

# Import after path setup - pylint: disable=wrong-import-position
from backend.main import app  # noqa: E402
from backend.repo import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_db() -> None:
    init_db()


@pytest.fixture
def client() -> t.Generator[TestClient, None, None]:
    """Provide test client for API testing.

    :return: Test client generator.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_refresh_token_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    monkeypatch.setenv(
        "SEEDS_FILE",
        str(repo_root / "seeds" / "narratives.seed.json"),
    )


@pytest.fixture(autouse=True)
def _clear_refresh_module_state() -> None:
    """Clear refresh module global state between tests for isolation.

    This ensures that the idempotency state doesn't leak between tests.
    """
    # Import here to avoid circular imports
    import backend.api.routes.refresh as refresh_module

    # Reset the module-level global state
    refresh_module.current_running_job = None
    refresh_module.last_completed_job = None
    refresh_module.last_started_ts = 0.0
