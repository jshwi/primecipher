"""Tests for CoinGecko source functionality."""

import importlib
import typing as t

import httpx
import pytest


def reload_src(
    monkeypatch: pytest.MonkeyPatch,
    ttl: str = "60",
    mode: str = "test",
    client_factory: t.Callable[[], t.Any] | None = None,
) -> t.Any:
    """Reload source module with new configuration.

    :param monkeypatch: Pytest fixture for patching.
    :param ttl: Time to live for cache.
    :param mode: Source mode to use.
    :param client_factory: Optional factory for fake HTTP client.
    :return: Source module with updated configuration.
    """
    monkeypatch.setenv("SOURCE_TTL", ttl)
    monkeypatch.setenv("SOURCE_MODE", mode)
    import backend.adapters.source as src  # pylint: disable=reimported

    importlib.reload(src)
    src._raw_cache.clear()

    # if a fake client factory is passed, patch httpx.client
    if client_factory:
        monkeypatch.setattr(httpx, "Client", client_factory)

    return src


class FakeResponse:
    """Fake HTTP response for testing.

    :param js: JSON data to return.
    """

    def __init__(self, js: dict) -> None:
        self._js = js

    def raise_for_status(self) -> bool:
        """Simulate successful status.

        :return: True if status is successful.
        """
        return True

    def json(self) -> dict:
        """Return JSON data.

        :return: JSON data dictionary.
        """
        return self._js


class FakeClient:
    """Context manager wrapper for a fake get() function.

    :param get_func: Function to handle GET requests.
    """

    def __init__(
        self,
        get_func: t.Callable[[str, dict], FakeResponse],
    ) -> None:
        self._get = get_func

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_: t.Any) -> t.Literal[False]:
        return False

    def get(self, url: str, params: dict | None = None) -> FakeResponse:
        """Execute the fake GET request.

        :param url: Request URL.
        :param params: Request parameters.
        :return: Fake response object.
        """
        return self._get(url, params or {})


def make_resp(js: dict) -> FakeResponse:
    """Create a fake response with given JSON data.

    :param js: JSON data to include in response.
    :return: Fake response object.
    """
    return FakeResponse(js)


def test_cg_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CoinGecko happy path with normal response.

    :param monkeypatch: Pytest fixture for patching.
    """

    # normal case: coins returned
    def fake_get(_: str, __: dict) -> FakeResponse:
        return make_resp(
            {"coins": [{"name": "Foxtrot", "market_cap_rank": 8}]},
        )

    src = reload_src(
        monkeypatch,
        ttl="120",
        mode="coingecko",
        client_factory=lambda *_, **__: FakeClient(fake_get),
    )
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    assert isinstance(out, list)
    assert out[0]["parent"].lower() == "foxtrot"


def test_cg_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CoinGecko fallback to deterministic when no results.

    :param monkeypatch: Pytest fixture for patching.
    """

    # api returns no coins -> fallback to deterministic
    def fake_get(_: str, __: dict) -> FakeResponse:
        return make_resp({"coins": []})

    src = reload_src(
        monkeypatch,
        ttl="120",
        mode="coingecko",
        client_factory=lambda *_, **__: FakeClient(fake_get),
    )
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    assert isinstance(out, list)
    assert len(out) > 0


def test_cg_network_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CoinGecko fallback to deterministic on network error.

    :param monkeypatch: Pytest fixture for patching.
    """

    # simulate network failure by raising inside get()
    def fake_get(_: str, __: dict) -> FakeResponse:
        raise httpx.RequestError("boom", request=None)

    src = reload_src(
        monkeypatch,
        ttl="120",
        mode="coingecko",
        client_factory=lambda *_, **__: FakeClient(fake_get),
    )
    s = src.Source(provider="coingecko")
    out = s.parents_for("dogs", ["dog"])
    # should not raise; should fallback to deterministic
    assert isinstance(out, list)
    assert len(out) > 0
