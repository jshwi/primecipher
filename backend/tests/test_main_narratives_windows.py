from fastapi.testclient import TestClient
import app.main as main


def test_narratives_windows_matrix():
    windows = ["1h", "24h", "7d", "bad"]
    with TestClient(main.app) as client:
        for w in windows:
            r = client.get("/narratives", params={"source": "file", "window": w})
            assert r.status_code in (200, 404)
