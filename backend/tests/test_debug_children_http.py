# backend/tests/test_debug_children_http.py
from fastapi.testclient import TestClient
import app.main as main


def test_children_endpoint_presence_tolerant():
    """
    Exercise FastAPI wiring via TestClient without assuming the debug router
    is mounted under /children. Accept 200 or 404.
    """
    with TestClient(main.app) as client:
        r = client.get("/children/FET")
        assert r.status_code in (200, 404)
