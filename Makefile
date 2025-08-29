FILES := $(shell git ls-files)
PY_FILES := $(shell git ls-files "backend/**/*.py")

VENV := backend/.venv/bin/activate

.PHONY: all
all: .make/hooks

$(VENV): backend/requirements.txt
	@python -m venv backend/.venv
	@backend/.venv/bin/pip install -r backend/requirements.txt
	@touch $@

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

.PHONY: hooks
#: install pre-commit hooks
hooks: .make/hooks

.PHONY: cov
#: check coverage
cov: $(VENV) $(PY_FILES)
	@PYTHONPATH=backend backend/.venv/bin/pytest backend/tests \
		--cov=backend/app --cov-report=term-missing \
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

.PHONY: clean
#: clean generated files
clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@rm -rf .coverage
	@rm -rf .git/hooks/*
	@rm -rf .make
	@rm -rf .venv
	@rm -rf *.log
