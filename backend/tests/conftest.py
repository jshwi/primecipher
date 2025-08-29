import os, sys, pytest
from pathlib import Path
import pytest

# Set env BEFORE importing app modules
here = Path(__file__).parent
repo_root = (here / "..").resolve()
os.environ.setdefault("SEEDS_FILE", str(repo_root / "seeds" / "narratives.seed.json"))
os.environ.setdefault("SOURCE_MODE", "test")  # deterministic adapter mode for tests

# Now import app after env is set
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.repo import init_db  # noqa
from app.main import app      # noqa

@pytest.fixture(scope="session", autouse=True)
def _init_db():
    init_db()

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

@pytest.fixture(autouse=True)
def _clear_refresh_token_env(monkeypatch):
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
