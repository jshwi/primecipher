PY_FILES := $(shell git ls-files "backend/**/*.py")

VENV := backend/.venv/bin/activate

.PHONY: all
all: .make/pre-commit

$(VENV): backend/requirements.txt
	@python -m venv backend/.venv
	@backend/.venv/bin/pip install -r backend/requirements.txt
	@touch $@

.make/hooks: $(VENV)
	@.venv/bin/pre-commit install \
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

.PHONY: pre-commit
#: install pre-commit hooks
hooks: .make/pre-commit

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


.make/smoke: $(VENV) $(PY_FILES)
	@bash scripts/smoke.sh
	@mkdir -p $(@D)
	@touch $@

.PHONY: smoke
#: run smoke test
smoke: .make/smoke

.PHONY: clean
#: clean generated files
clean:
	@find . -name '__pycache__' -exec rm -rf {} +
	@rm -rf .coverage
	@rm -rf .git/hooks/*
	@rm -rf .make
	@rm -rf .venv
