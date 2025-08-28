import os, sys, pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.repo import init_db

@pytest.fixture(scope="session", autouse=True)
def set_env_and_db():
    here = Path(__file__).parent
    repo_root = (here / "..").resolve()
    os.environ["SEEDS_FILE"] = str(repo_root / "seeds" / "narratives.seed.json")
    init_db()

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    # key fix: don't re-raise server exceptions; return 500 response instead
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
