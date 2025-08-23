# Testing cheatsheet

## Local quick runs
```bash
make test        # pytest -q
make cov         # pytest with coverage and CI-like hooks
PYTHONPATH=backend pytest -q backend/tests -k name
