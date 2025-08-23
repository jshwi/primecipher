from fastapi.testclient import TestClient
import app.main as main


def test_routes_registered_and_lifespan_runs():
    with TestClient(main.app) as client:
        # Collect route paths safely across FastAPI/Starlette versions
        paths = {
            getattr(r, "path_format", getattr(r, "path", ""))
            for r in main.app.router.routes
        }

        # These two are part of your API contract
        assert any(p.startswith("/narratives") for p in paths)
        assert any(p.startswith("/parents/") or p == "/parents" for p in paths)

        # Health endpoint should be live
        r_health = client.get("/healthz")
        assert r_health.status_code == 200

        # Root handler is optional; accept common statuses
        r_root = client.get("/")
        assert r_root.status_code in (200, 204, 307, 404)
