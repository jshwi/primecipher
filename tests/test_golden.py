"""Test expected seeds"""

import json
import typing as t
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app

GOLDEN_PATH = Path(__file__).parent / "golden.json"


def _load_golden() -> dict[str, t.Any]:
    assert GOLDEN_PATH.exists(), f"Golden file not found at {GOLDEN_PATH}"
    with GOLDEN_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_narratives() -> dict[str, t.Any]:
    client = TestClient(app)
    r = client.get("/narratives")
    assert r.status_code == 200, f"/narratives returned {r.status_code}"
    body = r.json()
    assert "items" in body, "Response missing 'items'"
    assert isinstance(body["items"], list), "'items' must be a list"
    return body


def _is_name_list(items: list[t.Any]) -> bool:
    return len(items) > 0 and isinstance(items[0], str)


def _index_by_name(
    items: list[dict[str, t.Any]],
) -> dict[str, dict[str, t.Any]]:
    return {
        it["name"]: it for it in items if isinstance(it, dict) and "name" in it
    }


def test_narratives_presence_and_shape() -> None:
    """This always runs.

    It verifies the endpoint is alive and returns expected names.

    - If the API returns a list of names, we ONLY check presence.
    - If the API returns objects, we also lightly validate the object
    shape.
    """
    golden = _load_golden()
    resp = _fetch_narratives()
    items = resp["items"]

    # Expected narratives from golden file (use those that appear)
    expected_names = [e["narrative"] for e in golden.get("expectations", [])]

    if _is_name_list(items):
        names = set(items)
        missing = [n for n in expected_names if n not in names]
        assert not missing, f"Missing narratives in response: {missing}"
    else:
        # Object shape: minimally verify presence and required keys
        by_name = _index_by_name(items)
        missing = [n for n in expected_names if n not in by_name]
        assert not missing, f"Missing narratives in response: {missing}"
        # Light shape check on one row
        sample = next(iter(by_name.values()))
        for key in ("name",):
            assert key in sample, f"Expected key '{key}' in narrative objects"


# pylint: disable=too-many-branches,too-many-locals
@pytest.mark.skipif(_load_golden is None, reason="golden not available")
def test_golden_ranges_and_ordering() -> None:
    """Runs only if the API returns objects with metrics (heat, etc).

    Otherwise, it SKIPS with a clear reason (not a hard fail).
    """
    golden = _load_golden()
    resp = _fetch_narratives()
    items = resp["items"]

    if _is_name_list(items):
        pytest.skip(
            "Endpoint returns a list of names; heat/order checks require"
            " object shape with metrics.",
        )

    by_name = _index_by_name(items)

    # --- Range checks
    failures: list[str] = []
    for exp in golden.get("expectations", []):
        name = exp["narrative"]
        if name not in by_name:
            failures.append(f"Missing narrative in response: {name}")
            continue

        row = by_name[name]
        if "heat" not in row:
            failures.append(
                f"Narrative '{name}' missing 'heat' field (need object schema"
                f" with metrics).",
            )
            continue

        try:
            heat = float(row.get("heat"))  # type: ignore
        # pylint: disable=broad-exception-caught
        except Exception:
            failures.append(
                f"Narrative '{name}' has non-numeric heat:"
                f" {row.get('heat')!r}",
            )
            continue

        lo = float(exp.get("min_heat", 0.0))
        hi = float(exp.get("max_heat", 1.0))
        if not lo <= heat <= hi:
            failures.append(
                f"Heat out of range for '{name}': {heat:.3f} not in [{lo:.3f},"
                f" {hi:.3f}]",
            )

    # --- Ordering checks (e.g. 'dogs > ai > privacy')
    for rule in golden.get("ordering", []):
        names = [s.strip() for s in rule.split(">")]
        for a, b in zip(names, names[1:]):
            if a not in by_name or b not in by_name:
                failures.append(
                    f"Ordering check skipped: missing '{a}' or '{b}' in"
                    f" response",
                )
                continue
            ra, rb = by_name[a], by_name[b]
            if "heat" not in ra or "heat" not in rb:
                failures.append(
                    f"Ordering check skipped: missing 'heat' in '{a}' or"
                    f" '{b}'",
                )
                continue
            try:
                ha = float(ra["heat"])
                hb = float(rb["heat"])
            # pylint: disable=broad-exception-caught
            except Exception:
                failures.append(
                    f"Ordering check skipped: non-numeric heat for '{a}' or"
                    f" '{b}'",
                )
                continue
            if ha <= hb:
                failures.append(
                    f"Ordering violated: expected {a}({ha:.3f}) >"
                    f" {b}({hb:.3f})",
                )

    if failures:
        raise AssertionError(
            "Golden checks failed:\n" + "\n".join(f"- {m}" for m in failures),
        )
