.PHONY: test cov

test:
	PYTHONPATH=backend pytest -q backend/tests

cov:
	PYTHONPATH=backend pytest backend/tests \
		--cov=backend/app --cov-report=term-missing
