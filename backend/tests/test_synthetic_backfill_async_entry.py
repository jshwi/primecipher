import importlib
import asyncio
import argparse
from types import SimpleNamespace

mod = importlib.import_module("app.tools.synthetic_backfill")

def test_synthetic_backfill_main_invokes_even_if_async(monkeypatch, tmp_path):
    # Avoid pytest args leaking into argparse inside main()
    monkeypatch.setattr("sys.argv", ["synthetic_backfill"], raising=False)
    # Stub parse_args to safe defaults (no FS/network)
    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self: SimpleNamespace(window="h1", narrative=None, parent=None, max=1),
        raising=False,
    )
    # Sandbox any incidental writes
    monkeypatch.chdir(tmp_path)
    main_fn = getattr(mod, "main", None)
    # Call if present; then try to resolve coroutine unconditionally
    val = main_fn and main_fn()
    try:
        # If val is a coroutine, this will run it; otherwise raises TypeError
        val = asyncio.run(val)
    except Exception:
        # Non-coroutines (or already running loop) just keep original val
        pass
    assert (main_fn is None) or (val is None or isinstance(val, (dict, list, str, int, float)))
