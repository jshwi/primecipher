# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================
VERSION := 0.71.0

# =============================================================================
# TOOL PATHS
# =============================================================================
POETRY := bin/poetry/bin/poetry

# =============================================================================
# FILE COLLECTIONS
# =============================================================================
FILES := $(shell git ls-files)
PY_FILES := $(shell git ls-files "*.py" ':!:whitelist.py')
PY_PROD_FILES := $(shell git ls-files "backend/*.py")
PY_TEST_FILES := $(shell git ls-files "tests/*.py")
JS_ALL_FILES := $(shell git ls-files | grep -E '\.js$$|\.jsx$$|\.ts$$|\.tsx$$')
JS_PROD_FILES := $(shell echo $(JS_FILES) | grep -E 'src')
JS_TEST_FILES := $(shell echo $(JS_FILES) | grep -E '__tests__')
JS_CONF_FILES := $(shell echo $(JS_FILES) | grep -E 'jest')

# =============================================================================
# DEPENDENCY FILES
# =============================================================================
PY_LOCK := poetry.lock
JS_LOCK := package-lock.json
PY_CONFIG := pyproject.toml
PY_WHITELIST := whitelist.py

# =============================================================================
# BUILD ARTIFACTS
# =============================================================================
PY_MODULES := .venv/bin/activate
JS_MODULES := node_modules/.package-lock.json
REPO_ARCHIVE := archive.zip
PY_COV := coverage.xml
PY_TYPES := .mypy_cache/CACHEDIR.TAG

# =============================================================================
# TASK MARKERS
# =============================================================================
PY_LINT := .make/lint/py
JS_LINT := .make/lint/js
PY_FORMAT := .make/format/py
PY_UNUSED := .make/unused
JS_COV := .make/coverage/js
PRE_COMMIT := .make/pre-commit

# =============================================================================
# COMMON COMMANDS
# =============================================================================
PY_RUN := $(POETRY) run
JS_RUN := npm run

# =============================================================================
# PHONY TARGETS
# =============================================================================
.PHONY: all lint frontend api deps-update clean cov build hooks unused test help

# =============================================================================
# MAIN TARGETS
# =============================================================================
all: $(PRE_COMMIT) $(JS_MODULES)

#: show this help message
help:
	@echo "Available targets:"
	@echo "  all          - Set up project (install deps, hooks)"
	@echo "  frontend     - Start frontend development server"
	@echo "  api          - Start API development server"
	@echo "  lint         - Run all linting checks"
	@echo "  cov          - Run tests with coverage"
	@echo "  build        - Run all quality checks"
	@echo "  clean        - Remove all generated files"
	@echo "  deps-update  - Update all dependencies"
	@echo "  hooks        - Install pre-commit hooks"
	@echo "  unused       - Check for unused code"

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================
#: start frontend development server
frontend: $(JS_MODULES)
	@$(JS_RUN) dev

#: start API development server
api: $(PY_MODULES)
	@$(PY_RUN) uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

#: update all dependencies
deps-update:
	@$(POETRY) update

# =============================================================================
# QUALITY ASSURANCE TARGETS
# =============================================================================
#: run all linting checks
lint: $(PY_LINT) $(JS_LINT)

#: run all tests with coverage
cov: $(PY_COV) $(JS_COV)

#: run all quality checks
build: $(PY_FORMAT) $(PY_LINT) $(PY_UNUSED) $(PY_TYPES) $(PY_COV)
	@touch $@

#: check for unused code
unused: $(PY_UNUSED) $(JS_UNUSED)

# =============================================================================
# UTILITY TARGETS
# =============================================================================
#: clean all generated files
clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@rm -rf .coverage .make .mypy_cache .pytest_cache .venv bin coverage.xml
	@rm -rf .git/hooks/*

#: install pre-commit hooks
hooks: $(PRE_COMMIT)

# =============================================================================
# DEPENDENCY TARGETS
# =============================================================================
$(PY_MODULES): $(POETRY) $(PY_LOCK)
	@[ ! $$(basename "$$($< env info --path)") = ".venv" ] && rm -rf "$$($< env info --path)" || exit 0
	@POETRY_VIRTUALENVS_IN_PROJECT=1 $< install
	@touch $@

$(JS_MODULES): $(JS_LOCK)
	@$(JS_RUN) install
	@touch $@

$(POETRY):
	@curl -sSL https://install.python-poetry.org | POETRY_HOME="$$(pwd)/bin/poetry" "$$(which python)" - --version 2.1.1
	@touch $@

# =============================================================================
# HOOK TARGETS
# =============================================================================
$(PRE_COMMIT): $(PY_MODULES)
	@$(PY_RUN) pre-commit install \
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

# =============================================================================
# FORMATTING TARGETS
# =============================================================================
$(PY_FORMAT): $(PY_MODULES) $(PY_FILES)
	@$(PY_RUN) black $(PY_FILES)
	@$(PY_RUN) flynt $(PY_FILES)
	@$(PY_RUN) isort $(PY_FILES)
	@mkdir -p $(@D)
	@touch $@

# =============================================================================
# LINTING TARGETS
# =============================================================================
$(PY_LINT): $(PY_MODULES) $(PY_FILES)
	@$(PY_RUN) pylint --output-format=colorized $(PY_FILES)
	@$(PY_RUN) docsig $(PY_FILES)
	@mkdir -p $(@D)
	@touch $@

$(JS_LINT): $(JS_MODULES) $(JS_FILES)
	@$(JS_RUN) next lint
	@mkdir -p $(@D)
	@touch $@

# =============================================================================
# TYPE CHECKING TARGETS
# =============================================================================
$(PY_TYPES): $(PY_MODULES) $(PY_FILES)
	@$(PY_RUN) mypy $(PY_FILES)
	@touch $@

# =============================================================================
# UNUSED CODE TARGETS
# =============================================================================
$(PY_UNUSED): $(PY_WHITELIST)
	@$(PY_RUN) vulture whitelist.py backend tests
	@mkdir -p $(@D)
	@touch $@

$(JS_UNUSED): $(JS_MODULES) $(JS_PROD_FILES) $(JS_TEST_FILES)
	@$(JS_RUN) unused
	@mkdir -p $(@D)
	@touch $@

$(PY_WHITELIST): $(PY_MODULES) $(PY_PROD_FILES) $(PY_TEST_FILES)
	@$(PY_RUN) vulture --make-whitelist backend tests > $@ || exit 0

# =============================================================================
# COVERAGE TARGETS
# =============================================================================
$(PY_COV): $(PY_MODULES) $(PY_PROD_FILES) $(PY_TEST_FILES)
	@$(PY_RUN) pytest tests --cov=backend && $(POETRY_RUN) coverage xml

$(JS_COV): $(JS_MODULES) $(JS_PROD_FILES) $(JS_TEST_FILES) $(JS_CONF_FILES)
	@$(NPM_RUN) jest
	@mkdir -p $(@D)
	@touch $@

# =============================================================================
# LOCK FILE TARGETS
# =============================================================================
$(PY_LOCK): $(PY_CONFIG)
	@$(POETRY) lock
	@touch $@

# =============================================================================
# ARCHIVE TARGETS
# =============================================================================
$(REPO_ARCHIVE): $(FILES)
	@git archive --format=zip --output $@ HEAD
