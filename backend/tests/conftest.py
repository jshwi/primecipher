import os, json, tempfile, pytest
from datetime import datetime, timezone

@pytest.fixture(scope="session")
def _tmp_dirs():
    d = tempfile.TemporaryDirectory()
    data_dir = os.path.join(d.name, "data")
    seeds_dir = os.path.join(d.name, "seeds")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(seeds_dir, exist_ok=True)
    yield {"data": data_dir, "seeds": seeds_dir, "_tmp": d}
    d.cleanup()

@pytest.fixture(scope="session")
def app_client(_tmp_dirs):
    os.environ["DATA_DIR"] = _tmp_dirs["data"]
    os.environ["SEED_DIR"] = _tmp_dirs["seeds"]
    os.environ["SNAPSHOT_DB_PATH"] = os.path.join(_tmp_dirs["data"], "snapshots.db")

    now = datetime.now(timezone.utc).isoformat()

    # narratives (24h)
    narratives = [
        {
            "narrative": "dogs", "heatScore": 12.3, "window": "24h",
            "signals": {"onchainVolumeUsd": 0.0, "onchainLiquidityUsd": 0.0, "ctMentions": 0},
            "parents": ["WIF","MOODENG"], "lastUpdated": now
        },
        {
            "narrative": "ai", "heatScore": 22.1, "window": "24h",
            "signals": {"onchainVolumeUsd": 0.0, "onchainLiquidityUsd": 0.0, "ctMentions": 0},
            "parents": ["FET","TAO"], "lastUpdated": now
        },
    ]
    with open(os.path.join(_tmp_dirs["data"], "narratives-24h.json"), "w") as f:
        json.dump(narratives, f)

    # parents for ai (24h)
    parents_ai = [
        {
            "parent": "FET", "narrative": "ai", "childrenCount": 0, "childrenNew24h": 0,
            "survivalRates": {"h24": 0.0, "d7": 0.0},
            "liquidityFunnel": {"parentLiquidityUsd": 0.0, "childrenLiquidityUsd": 0.0},
            "topChild": {"symbol": None, "liquidityUsd": 0.0, "volume24hUsd": 0.0,
                         "ageHours": None, "holders": None, "matched": None},
            "lastUpdated": now
        },
        {
            "parent": "TAO", "narrative": "ai", "childrenCount": 0, "childrenNew24h": 0,
            "survivalRates": {"h24": 0.0, "d7": 0.0},
            "liquidityFunnel": {"parentLiquidityUsd": 0.0, "childrenLiquidityUsd": 0.0},
            "topChild": {"symbol": None, "liquidityUsd": 0.0, "volume24hUsd": 0.0,
                         "ageHours": None, "holders": None, "matched": None},
            "lastUpdated": now
        },
    ]
    with open(os.path.join(_tmp_dirs["data"], "parents-ai-24h.json"), "w") as f:
        json.dump(parents_ai, f)

    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c

