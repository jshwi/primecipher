class _FakeCursor:
    def __init__(self):
        self._one = None
        # Dict-shaped rows so code can do r["pair_address"]
        self._rows = [
            {"pair_address": "PAIR_MATCHED"},
            {"pair_address": "PAIR_OTHER"},
        ]
        self.last_sql = ""
        self.last_args = []

    def execute(self, sql, args=None):
        self.last_sql = sql
        self.last_args = list(args or [])
        # Return self so .fetchall() works
        return self

    def fetchone(self):
        return self._one

    def fetchall(self):
        # Always return the dict rows; the test validates SQL/args were built
        return list(self._rows)

class _FakeConn:
    def __init__(self):
        self._cursor = _FakeCursor()
    def cursor(self):
        return self._cursor
    def execute(self, *a, **kw):
        return self._cursor.execute(*a, **kw)
    def commit(self): pass
    def close(self): pass

def test_recent_pairs_applies_parents_and_narrative(monkeypatch):
    import app.storage as storage

    # Use fake DB connection
    fake = _FakeConn()
    monkeypatch.setattr(storage, "connect", lambda: fake, raising=False)

    # Call with both filters to hit those branches
    parents = ["WIF", "FET"]
    narrative = "ai"
    out = storage.recent_pairs(max_idle_hours=24.0, parents=parents, narrative=narrative)

    # We should still get the shaped list
    assert isinstance(out, list) and len(out) == 2

    # Verify the SQL was extended with both filters and args appended correctly
    sql = fake._cursor.last_sql
    args = fake._cursor.last_args

    # 1st arg is the cutoff timestamp; the rest correspond to parents then narrative
    assert isinstance(args[0], int) and args[0] > 0
    assert parents[0] in args and parents[1] in args and narrative in args

    # Ensure parent placeholders were added (",?" for each parent) and narrative clause present
    assert " AND parent IN (" in sql and sql.count("?") >= 1 + len(parents) + 1  # cutoff + parents + narrative
    assert " AND narrative = ?" in sql
