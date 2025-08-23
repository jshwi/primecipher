#!/usr/bin/env python3
import importlib
import inspect
import sys
from types import ModuleType
from typing import Any


def is_defined_in(module: ModuleType, obj: Any) -> bool:
    """True if obj is defined in the given module (not imported)."""
    try:
        return getattr(obj, "__module__", "") == module.__name__
    except Exception:
        return False


def list_module_members(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return

    print(f"== {module_name} ==")
    # Top-level functions
    for name, obj in sorted(
        ((n, o) for n, o in vars(mod).items() if inspect.isfunction(o) and is_defined_in(mod, o)),
        key=lambda x: x[0],
    ):
        try:
            sig = str(inspect.signature(obj))
        except (ValueError, TypeError):
            sig = "()"
        print(f"def {name}{sig}")

    # Top-level classes (and their methods) defined here
    for name, cls in sorted(
        ((n, o) for n, o in vars(mod).items() if inspect.isclass(o) and is_defined_in(mod, o)),
        key=lambda x: x[0],
    ):
        print(f"class {name}")
        for m_name, m_obj in sorted(
            ((mn, mo) for mn, mo in vars(cls).items() if inspect.isfunction(mo) and is_defined_in(mod, mo)),
            key=lambda x: x[0],
        ):
            try:
                sig = str(inspect.signature(m_obj))
            except (ValueError, TypeError):
                sig = "()"
            print(f"  def {m_name}{sig}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scripts/list_functions.py app.module [app.other_module ...]")
        sys.exit(1)

    # Ensure we can import `app.*`
    if "backend" not in sys.path:
        sys.path.insert(0, "backend")

    for mod in sys.argv[1:]:
        list_module_members(mod)
