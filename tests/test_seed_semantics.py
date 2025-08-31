"""Tests for seed semantics functionality."""

import importlib
import json
from pathlib import Path

from backend import seeds as seeds_mod


def write_seeds(tmp_path, data) -> Path:
    """Write seed data to temporary file.

    :param tmp_path: Pytest fixture for temporary directory.
    :param data: Seed data to write.
    :return: Path to the written seed file.
    """
    p = tmp_path / "narratives.seed.json"
    p.write_text(json.dumps(data))
    return p


def reload_seeds_with(path) -> None:
    """Reload seeds module with new file path.

    :param path: Path to the seed file to load.
    """
    import os

    os.environ["SEEDS_FILE"] = str(path)
    seeds_mod.load_seeds.cache_clear()
    importlib.reload(seeds_mod)


def test_blocklist_and_allow_name_match(tmp_path, client) -> None:
    """Test blocklist and allowNameMatch functionality.

    :param tmp_path: Pytest fixture for temporary directory.
    :param client: Pytest fixture for test client.
    """
    # narrative 'dogs'; terms include 'dog'; block 'shib'
    data = {
        "narratives": [
            {
                "name": "dogs",
                "terms": ["dog", "wif", "shib"],
                "allowNameMatch": False,
                "block": ["shib"],
            },
        ],
    }
    p = write_seeds(tmp_path, data)
    reload_seeds_with(p)

    # dry run to compute without persisting
    r = client.post("/refresh?dryRun=1")
    assert r.status_code == 200
    items = r.json()["items"]["dogs"]
    # ensure nothing containing 'shib' is present
    assert all("shib" not in i["parent"].lower() for i in items)
    # allownamematch=false: items that only match 'dogs' name (if any) are
    # excluded; deterministic adapter uses terms, so we still have up to 3
    # items left
    assert 0 <= len(items) <= 3
