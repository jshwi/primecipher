VERSION := 0.71.0

POETRY := bin/poetry/bin/poetry

PYTHON_FILES := $(shell git ls-files "*.py" ':!:whitelist.py')
PYTHON_PACKAGE_FILES := $(shell git ls-files "backend/*.py")
PYTHON_TEST_FILES := $(shell git ls-files "tests/*.py")
DOCS_FILES := $(shell git ls-files "docs/*.rst" "docs/*.md")
JS_FILES := $(shell git ls-files | grep -E '\.js$$|\.jsx$$|\.ts$$|\.tsx$$')
JS_PACKAGE_FILES := $(shell echo $(JS_FILES) | grep -E 'src')
TEST_JS_FILES := $(shell echo $(JS_FILES) | grep -E '__tests__')
TEST_CONFIG := $(shell echo $(JS_FILES) | grep -E 'jest')

PY_LINT := .make/lint/py
JS_LINT := .make/lint/js
PRE_COMMIT := .make/pre-commit
PY_TYPES := .mypy_cache/CACHEDIR.TAG
PY_UNUSED := .make/unused
PY_COV := coverage.xml
JS_COV := .make/coverage/js
JS_MODULES := node_modules/.package-lock.json
PY_MODULES := .venv/bin/activate
PY_LOCK := poetry.lock
JS_LOCK := package-lock.json
PY_WHITELIST := whitelist.py
REPO_ARCHIVE := archive.zip
PY_FORMAT := .make/format/py
PY_CONFIG := pyproject.toml
MYPY := .mypy_cache/CACHEDIR.TAG

.PHONY: all lint frontend api deps-update clean cov build hooks unused

all: $(PRE_COMMIT) $(JS_MODULES)

lint: $(PY_LINT) $(JS_LINT)

#: start frontend
frontend: $(JS_MODULES)
	@npm run dev

#: start api
api: $(PY_MODULES)
	@$(POETRY) run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

#: update dependencies
deps-update:
	@$(POETRY) update

#: clean compiled files
clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@rm -rf .coverage
	@rm -rf .git/hooks/*
	@rm -rf .make
	@rm -rf .mypy_cache
	@rm -rf .pytest_cache
	@rm -rf .venv
	@rm -rf bin
	@rm -rf coverage.xml

#: test source
cov: $(PY_COV) $(JS_COV)

#: run all checks
build: $(PY_FORMAT) $(PY_LINT) $(PY_UNUSED) $(PY_TYPES) $(PY_COV)
	@touch $@

#: install pre-commit hooks
hooks: $(PRE_COMMIT)

#: check for unused code
unused: $(PY_UNUSED) $(JS_UNUSED)

$(PY_MODULES): $(POETRY) $(PY_LOCK)
	@[ ! $$(basename "$$($< env info --path)") = ".venv" ] && rm -rf "$$($< env info --path)" || exit 0
	@POETRY_VIRTUALENVS_IN_PROJECT=1 $< install
	@touch $@

$(JS_MODULES): $(JS_LOCK)
	@npm install
	@touch $@

$(PRE_COMMIT): $(PY_MODULES)
	@$(POETRY) run pre-commit install \
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

$(POETRY):
	@curl -sSL https://install.python-poetry.org | POETRY_HOME="$$(pwd)/bin/poetry" "$$(which python)" - --version 2.1.1
	@touch $@

$(PY_FORMAT): $(PY_MODULES) $(PYTHON_FILES)
	@$(POETRY) run black $(PYTHON_FILES)
	@$(POETRY) run flynt $(PYTHON_FILES)
	@$(POETRY) run isort $(PYTHON_FILES)
	@mkdir -p $(@D)
	@touch $@

$(PY_LINT): $(PY_MODULES) $(PYTHON_FILES)
	@$(POETRY) run pylint --output-format=colorized $(PYTHON_FILES)
	@$(POETRY) run docsig $(PYTHON_FILES)
	@mkdir -p $(@D)
	@touch $@

$(JS_LINT): $(JS_MODULES) $(JS_FILES)
	@npx next lint
	@mkdir -p $(@D)
	@touch $@

$(MYPY): $(PY_MODULES) $(PYTHON_FILES)
	@$(POETRY) run mypy $(PYTHON_FILES)
	@touch $@

$(PY_UNUSED): $(PY_WHITELIST)
	@$(POETRY) run vulture whitelist.py backend tests
	@mkdir -p $(@D)
	@touch $@

#: check for unused code
$(JS_UNUSED): $(JS_MODULES) $(JS_PACKAGE_FILES) $(JS_TEST_FILES)
	@npm run unused
	@mkdir -p $(@D)
	@touch $@

#: generate whitelist of allowed unused code
$(PY_WHITELIST): $(PY_MODULES) $(PYTHON_PACKAGE_FILES) $(PYTHON_TEST_FILES)
	@$(POETRY) run vulture --make-whitelist backend tests > $@ || exit 0

$(PY_COV): $(PY_MODULES) $(PYTHON_PACKAGE_FILES) $(PYTHON_TEST_FILES)
	@$(POETRY) run pytest tests --cov=backend && $(POETRY) run coverage xml

$(JS_COV): $(JS_MODULES) $(JS_PACKAGE_FILES) $(JS_TEST_FILES) $(TEST_CONFIG)
	@npx jest
	@mkdir -p $(@D)
	@touch $@

#: poetry lock
$(POETRY_LOCK): $(PY_CONFIG)
	@$(POETRY) lock
	@touch $@

#: create a repo archive
$(REPO_ARCHIVE): $(FILES)
	@git archive --format=zip --output $@ HEAD

