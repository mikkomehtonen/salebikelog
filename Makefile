.PHONY: lint typecheck test verify format format-check coverage-ratchet ascii

VENV := .venv/bin

lint:
	$(VENV)/ruff check .

format:
	$(VENV)/ruff format .

format-check:
	$(VENV)/ruff format --check .

typecheck:
	$(VENV)/mypy app/ tests/

test:
	$(VENV)/pytest

coverage-ratchet:
	$(VENV)/python3 scripts/coverage_ratchet.py

ascii:
	bash scripts/check-ascii.sh

verify: format-check lint ascii typecheck test coverage-ratchet
