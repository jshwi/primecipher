"""Tests for parents pagination functionality."""

import base64
import json
import typing as t

import pytest


def _enc_cursor(n: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"o": n}).encode()).decode()


def _fake_many(
    _self: t.Any,
    _: str,
    __: list[str],
    **_kw: t.Any,
) -> list[dict]:
    # 150 ascending matches; route will cap to TOP_N=100
    return [{"parent": f"p{i:03d}", "matches": i} for i in range(150)]


def test_parents_pagination_two_pages(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test pagination across two pages.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    # patch source actually used by compute_all()
    import backend.parents as parents_mod

    monkeypatch.setattr(
        parents_mod.Source,
        "parents_for",
        _fake_many,
        raising=True,
    )

    # persist data (not dryrun) so route reads db path too
    r = client.post("/refresh")
    assert r.status_code == 200

    # page 1
    r1 = client.get("/parents/dogs?limit=25")
    assert r1.status_code == 200
    b1 = r1.json()
    assert len(b1["items"]) == 25
    assert b1["nextCursor"] is not None

    # page 2 via returned cursor
    cursor = b1["nextCursor"]
    r2 = client.get(f"/parents/dogs?limit=25&cursor={cursor}")
    assert r2.status_code == 200
    b2 = r2.json()
    assert len(b2["items"]) == 25
    # ensure no overlap between pages
    first_ids = {x["parent"] for x in b1["items"]}
    second_ids = {x["parent"] for x in b2["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_parents_pagination_end_of_list(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test pagination at end of list.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    import backend.parents as parents_mod

    monkeypatch.setattr(
        parents_mod.Source,
        "parents_for",
        _fake_many,
        raising=True,
    )
    client.post("/refresh")

    # jump close to end (100 capped items total)
    cursor = _enc_cursor(90)
    r = client.get(f"/parents/dogs?limit=25&cursor={cursor}")
    assert r.status_code == 200
    b = r.json()
    # only 10 remain (items 90..99)
    assert len(b["items"]) == 10
    assert b["nextCursor"] is None


def test_parents_invalid_cursor_400(client: t.Any) -> None:
    """Test that invalid cursor returns 400 error.

    :param client: Pytest fixture for test client.
    """
    r = client.get("/parents/dogs?cursor=not-base64")
    assert r.status_code == 400
    body = r.json()
    # your global handler wraps httpexception into {"ok": false, "error":
    # "..."}
    assert body.get("ok") is False
    assert "error" in body


def test_parents_cursor_missing_o_field_400(client: t.Any) -> None:
    """Test that cursor missing 'o' field returns 400 error.

    :param client: Pytest fixture for test client.
    """
    # create cursor with missing 'o' field
    bad_cursor = base64.urlsafe_b64encode(
        json.dumps({"offset": 10}).encode(),
    ).decode()
    r = client.get(f"/parents/dogs?cursor={bad_cursor}")
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False
    assert "error" in body


def test_parents_cursor_out_of_range_empty_page(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that cursor beyond available items returns empty page.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    import backend.parents as parents_mod

    monkeypatch.setattr(
        parents_mod.Source,
        "parents_for",
        _fake_many,
        raising=True,
    )
    client.post("/refresh")

    # cursor way beyond available items (100 capped)
    cursor = _enc_cursor(999999)
    r = client.get(f"/parents/dogs?cursor={cursor}")
    assert r.status_code == 200
    body = r.json()
    assert body["narrative"] == "dogs"
    assert body["items"] == []
    assert body["nextCursor"] is None


def test_parents_limit_clamping(
    client: t.Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that oversized limits are clamped to 100.

    :param client: Pytest fixture for test client.
    :param monkeypatch: Pytest fixture for patching.
    """
    import backend.parents as parents_mod

    monkeypatch.setattr(
        parents_mod.Source,
        "parents_for",
        _fake_many,
        raising=True,
    )
    client.post("/refresh")

    # request with limit > 100 should be clamped
    r = client.get("/parents/dogs?limit=9999")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) <= 100  # should be clamped to 100
