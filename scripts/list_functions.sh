#!/bin/bash
make backend/.venv/bin/activate >/dev/null 2>&1
source backend/.venv/bin/activate
PYTHONPATH=backend backend/.venv/bin/python lib/list_functions.py "${@}"
