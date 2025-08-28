import os, sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

@pytest.fixture(autouse=True, scope="session")
def set_seeds_env():
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, ".."))
    os.environ["SEEDS_FILE"] = os.path.join(repo_root, "seeds", "narratives.seed.json")

def client():
    return TestClient(app)
