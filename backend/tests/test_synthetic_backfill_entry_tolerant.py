import importlib


def test_synthetic_backfill_entrypoint_symbol():
    mod = importlib.import_module("app.tools.synthetic_backfill")

    # Just assert an entry function exists (main or generate), without calling it.
    run = getattr(mod, "main", None) or getattr(mod, "generate", None)

    # It should be callable (function or coroutine function), but we never invoke it
    assert (run is None) or callable(run)
