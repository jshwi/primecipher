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


ifeq ($(OS),Windows_NT)
	VENV := .venv/Scripts/activate
else
	VENV := .venv/bin/activate
endif
NODE_MODULES := node_modules/.package-lock.json

.PHONY: all
#: install development environment
all: .make/pre-commit $(NODE_MODULES)

#: build and check integrity of distribution
.PHONY: build
#: run all checks
build: .make/format \
	.make/lint \
	.make/unused \
	.mypy_cache/CACHEDIR.TAG \
	coverage.xml
	@touch $@

.PHONY: test
#: test source
cov: coverage.xml coverage/lcov.info

.PHONY: clean
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

#: generate virtual environment
$(VENV): $(POETRY) poetry.lock
	@[ ! $$(basename "$$($< env info --path)") = ".venv" ] \
		&& rm -rf "$$($< env info --path)" \
		|| exit 0
	@POETRY_VIRTUALENVS_IN_PROJECT=1 $< install
	@touch $@

#: install node modules
$(NODE_MODULES): package-lock.json
	@npm install

#: install pre-commit hooks
.make/pre-commit: $(VENV)
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

#: install poetry
$(POETRY):
	@curl -sSL https://install.python-poetry.org | \
		POETRY_HOME="$$(pwd)/bin/poetry" "$$(which python)" - --version 2.1.1
	@touch $@

#: run checks that format code
.make/format: $(VENV) $(PYTHON_FILES) $(NODE_MODULES) $(JS_FILES)
	@$(POETRY) run black $(PYTHON_FILES)
	@$(POETRY) run flynt $(PYTHON_FILES)
	@$(POETRY) run isort $(PYTHON_FILES)
	@mkdir -p $(@D)
	@touch $@

#: lint code
.make/lint: $(VENV) $(PYTHON_FILES) $(NODE_MODULES) $(JS_FILES)
	@$(POETRY) run pylint --output-format=colorized $(PYTHON_FILES)
	@$(POETRY) run docsig $(PYTHON_FILES)
	@npx next lint
	@mkdir -p $(@D)
	@touch $@

#: check typing
.mypy_cache/CACHEDIR.TAG: $(VENV) $(PYTHON_FILES)
	@$(POETRY) run mypy $(PYTHON_FILES)
	@touch $@

#: check for unused code
.make/unused: whitelist.py $(NODE_MODULES) $(JS_PACKAGE_FILES) $(JS_TEST_FILES)
	@$(POETRY) run vulture whitelist.py backend tests
	@npm run unused
	@mkdir -p $(@D)
	@touch $@

#: generate whitelist of allowed unused code
whitelist.py: $(VENV) $(PYTHON_PACKAGE_FILES) $(PYTHON_TEST_FILES)
	@$(POETRY) run vulture --make-whitelist backend tests > $@ || exit 0

#: generate coverage report
coverage.xml: $(VENV) $(PYTHON_PACKAGE_FILES) $(PYTHON_TEST_FILES)
	@$(POETRY) run pytest tests --cov=backend \
		&& $(POETRY) run coverage xml

coverage/lcov.info: $(NODE_MODULES) \
	$(JS_PACKAGE_FILES) \
	$(JS_TEST_FILES) \
	$(TEST_CONFIG)
	@npx jest
	@mkdir -p $(@D)
	@touch $@

#: poetry lock
poetry.lock: pyproject.toml
	@$(POETRY) lock
	@touch $@

.PHONY: deps-update
#: update dependencies
deps-update:
	@$(POETRY) update

.PHONY: api
#: start api
api: $(VENV)
	@$(POETRY) run uvicorn backend.main:app --host 0.0.0.0 --port 8000
