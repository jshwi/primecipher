import os, sys, pytest
from pathlib import Path

# import backend/ on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa
from app.repo import init_db  # noqa

@pytest.fixture(scope="session", autouse=True)
def set_env_and_db():
    here = Path(__file__).parent
    repo_root = (here / "..").resolve()
    os.environ["SEEDS_FILE"] = str(repo_root / "seeds" / "narratives.seed.json")
    init_db()

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    # using context manager triggers FastAPI startup events if defined
    with TestClient(app) as c:
        yield c
