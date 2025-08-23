class _FakeCursor:
    def __init__(self, rows=None):
        # Return dicts shaped like the real cursor.row_factory result
        # so recent_pairs() can do r["pair_address"].
        self.rows = rows or [
            {"pair_address": "PAIR1"},
            {"pair_address": "PAIR2"},
        ]
        self._one = None  # value for fetchone()

    def execute(self, sql, *args, **kwargs):
        if "first_seen FROM tracked_pairs" in sql:
            self._one = None  # simulate "not found" so upsert takes insert path
        return self

    def fetchone(self):
        return self._one

    def fetchall(self):
        return list(self.rows)


class _FakeConn:
    def __init__(self):
        self._cursor = _FakeCursor()

    def execute(self, *a, **kw):
        return self._cursor.execute(*a, **kw)

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def close(self):
        pass


def test_storage_crud_via_fake_connect(monkeypatch):
    import app.storage as storage

    # Route all DB work through our fake connection
    monkeypatch.setattr(storage, "connect", lambda: _FakeConn(), raising=False)

    # Basic path function; no FS access in test
    assert isinstance(storage._default_db_path(), str)

    # These calls should not raise with the fake connection in place
    storage.init_db()
    storage.insert_snapshot(
        pair_address="MintDemo1",
        ts=1724371200000,
        price_usd=1.23,
        liquidity_usd=456.0,
        fdv_usd=None,
        vol24h_usd=789.0,
    )
    storage.upsert_tracked_pair(
        pair_address="MintDemo1", parent="WIF", narrative="dogs", symbol="WIF"
    )

    out = storage.recent_pairs(max_idle_hours=72.0, parents=None, narrative=None)
    assert isinstance(out, list)
    assert len(out) == 2  # from our fake cursor's default rows
