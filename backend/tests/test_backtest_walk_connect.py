import importlib
import types


class _FakeConn:
    def __init__(self):
        self.row_factory = None


def test_backtest_walk_connect_calls_sqlite(monkeypatch):
    mod = importlib.import_module("app.backtest_walk")

    calls = {"n": 0}
    fake_sqlite = types.SimpleNamespace(
        Row=object,  # sentinel used by _connect to set row_factory
        connect=lambda *a, **k: (calls.__setitem__("n", calls["n"] + 1) or _FakeConn()),
    )
    monkeypatch.setattr(mod, "sqlite3", fake_sqlite, raising=False)

    conn = mod._connect()
    assert isinstance(conn, _FakeConn)
    assert calls["n"] == 1
    # ensure row_factory got assigned to our sentinel
    assert conn.row_factory is fake_sqlite.Row
