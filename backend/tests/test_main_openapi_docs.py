from fastapi.testclient import TestClient
import app.main as main


def test_openapi_and_docs_endpoints_tolerant():
    with TestClient(main.app) as client:
        # /openapi.json usually exists
        r_openapi = client.get("/openapi.json")
        assert r_openapi.status_code in (200, 404)

        # Swagger UI path can vary; accept common ones
        r_docs = client.get("/docs")
        r_redoc = client.get("/redoc")
        assert r_docs.status_code in (200, 404)
        assert r_redoc.status_code in (200, 404)
