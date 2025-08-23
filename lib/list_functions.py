#!/usr/bin/env python3
import importlib
import inspect
import pkgutil
import sys

def list_module_members(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return

    print(f"== {module_name} ==")
    for name, obj in inspect.getmembers(mod):
        if inspect.isfunction(obj):
            sig = str(inspect.signature(obj))
            print(f"def {name}{sig}")
        elif inspect.isclass(obj):
            print(f"class {name}")
            for m_name, m_obj in inspect.getmembers(obj, inspect.isfunction):
                sig = str(inspect.signature(m_obj))
                print(f"  def {m_name}{sig}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scripts/list_functions.py app.module [app.other_module ...]")
        sys.exit(1)

    sys.path.insert(0, "backend")  # so `app.*` can be imported
    for mod in sys.argv[1:]:
        list_module_members(mod)
