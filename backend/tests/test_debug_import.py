def test_debug_module_imports():
    import app.debug as dbg
    assert dbg is not None

    for attr in ("dump_env", "print_env", "noop"):
        fn = getattr(dbg, attr, None)
        if callable(fn):
            try:
                fn()
            except TypeError:
                pass
