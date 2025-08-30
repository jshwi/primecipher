SHELL := /bin/bash

.ONESHELL:

FILES := $(shell git ls-files)
PY_FILES := $(shell git ls-files "backend/**/*.py")
NODE_MODULES := frontend/node_modules/.package-lock.json

VENV := backend/.venv/bin/activate

.PHONY: all
all: .make/hooks

$(VENV): backend/requirements.txt
	@python -m venv backend/.venv
	@backend/.venv/bin/pip install -r backend/requirements.txt
	@touch $@

$(NODE_MODULES): frontend/package-lock.json
	@pushd frontend >/dev/null 2>&1
	@npm install
	@popd >/dev/null 2>&1

.make/hooks: $(VENV)
	@backend/.venv/bin/pre-commit install \
		--hook-type pre-commit \
		--hook-type pre-merge-commit \
		--hook-type pre-push \
		--hook-type prepare-commit-msg \
		--hook-type commit-msg \
		--hook-type post-commit \
		--hook-type post-checkout \
		--hook-type post-merge \
		--hook-type post-rewrite
	@mkdir -p $(@D)
	@touch $@

.PHONY: venv
#: create virtual environment and install dependencies
venv: $(VENV)

.PHONY: node
#: install node modules
node: $(NODE_MODULES)

.PHONY: hooks
#: install pre-commit hooks
hooks: .make/hooks

.PHONY: cov
#: check coverage
cov: $(VENV) $(PY_FILES)
	@PYTHONPATH=backend backend/.venv/bin/pytest backend/tests \
		--cov=backend/app --cov-report=term-missing \
		--cov-fail-under 100 \
		&& backend/.venv/bin/coverage xml

coverage.xml: $(VENV) $(PY_FILES)
	@make cov
	@touch $@

.PHONY: test
#: run tests
test: coverage.xml

archive.zip: $(FILES)
	@git archive --format=zip --output $@ HEAD

.PHONY: archive
#: zip repo into an archive
archive: archive.zip

.PHONY: api
#: start api server
api: $(VENV)
	@backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000

.PHONY: start
#: start dev server
start: $(NODE_MODULES)
	@pushd frontend >/dev/null 2>&1
	@npm run dev
	@popd >/dev/null 2>&1

.PHONY: clean
#: clean generated files
clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@rm -rf .coverage
	@rm -rf .git/hooks/*
	@rm -rf .make
	@rm -rf .venv
	@rm -rf *.log
