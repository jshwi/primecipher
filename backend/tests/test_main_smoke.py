from fastapi.testclient import TestClient
import app.main as main

def test_root_and_healthz_smoke():
    client = TestClient(main.app)

    # Root may or may not exist; accept 200 or 404
    r_root = client.get("/")
    assert r_root.status_code in (200, 404)

    # /healthz may or may not exist; accept 200 or 404
    r_health = client.get("/healthz")
    assert r_health.status_code in (200, 404)
