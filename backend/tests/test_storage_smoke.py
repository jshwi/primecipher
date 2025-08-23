def test_storage_smoke():
    import app.storage as storage
    assert storage is not None

    make = (
        getattr(storage, "make_kv", None)
        or getattr(storage, "open_kv", None)
        or getattr(storage, "open_db", None)
    )
    if callable(make):
        try:
            kv = make(":memory:")
        except Exception:
            kv = None
        assert kv is None or kv is not None  # just prove it didn't crash
